#import "ExcelNibArchive.h"
#import <objc/message.h>
#include <string.h>

static NSString *const EXNibDomain = @"ExcelPort.Nib";
static void EXNibFail(NSString *message) __attribute__((noreturn));
static void EXNibFail(NSString *message) {
    @throw [NSException exceptionWithName:@"EXNibFormatError" reason:message userInfo:nil];
}
static NSError *EXNibError(NSException *exception) {
    return [NSError errorWithDomain:EXNibDomain code:1 userInfo:@{NSLocalizedDescriptionKey: exception.reason ?: exception.name}];
}

typedef struct { const uint8_t *bytes; NSUInteger position, limit; } EXNibReader;
static const uint8_t *Take(EXNibReader *r, NSUInteger length) {
    if (r->position > r->limit || length > r->limit - r->position) EXNibFail(@"Truncated or overlapping nib table");
    const uint8_t *p = r->bytes + r->position; r->position += length; return p;
}
static uint64_t LE(EXNibReader *r, NSUInteger length) {
    const uint8_t *p = Take(r, length); uint64_t value = 0;
    for (NSUInteger i = 0; i < length; i++) value |= (uint64_t)p[i] << (i * 8);
    return value;
}
static uint32_t VarInt(EXNibReader *r) {
    uint32_t value = 0;
    for (NSUInteger i = 0; i < 5; i++) {
        uint8_t b = (uint8_t)LE(r, 1);
        if (i == 4 && (b & 0x70)) EXNibFail(@"Nib varint exceeds uint32");
        value |= (uint32_t)(b & 127) << (7 * i);
        if (b & 128) return value;
    }
    EXNibFail(@"Unterminated nib varint");
}
static void End(EXNibReader *r) { if (r->position != r->limit) EXNibFail(@"Unexpected bytes between nib tables"); }
static NSString *UTF8(const uint8_t *p, NSUInteger size) {
    NSString *s = [[NSString alloc] initWithBytes:p length:size encoding:NSUTF8StringEncoding];
    if (!s) EXNibFail(@"Invalid UTF-8 in nib"); return s;
}

NSDictionary *EXNibParse(NSData *data, NSError **error) {
    @try {
        if (data.length < 50 || data.length > 64 * 1024 * 1024 || memcmp(data.bytes, "NIBArchive", 10)) EXNibFail(@"Not a supported NIBArchive");
        EXNibReader h = {data.bytes, 10, data.length}; uint32_t v[10];
        for (NSUInteger i = 0; i < 10; i++) v[i] = (uint32_t)LE(&h, 4);
        if (v[0] != 1 || v[1] != 9) EXNibFail(@"Unsupported nib format/coder");
        NSUInteger oc=v[2], oo=v[3], kc=v[4], ko=v[5], vc=v[6], vo=v[7], cc=v[8], co=v[9];
        if (!(oo==50 && oo<=ko && ko<=vo && vo<=co && co<=data.length)) EXNibFail(@"Invalid nib offsets");
        if (oc>1000000 || kc>1000000 || vc>1000000 || cc>1000000) EXNibFail(@"Excessive nib counts");
        NSMutableArray *objects=[NSMutableArray array], *keys=[NSMutableArray array], *values=[NSMutableArray array], *classes=[NSMutableArray array];
        EXNibReader r={data.bytes,oo,ko};
        for (NSUInteger i=0; i<oc; i++) {
            uint32_t cls=VarInt(&r), start=VarInt(&r), count=VarInt(&r);
            [objects addObject:@{ @"class_index":@(cls), @"value_start":@(start), @"value_count":@(count) }];
        }
        End(&r); r=(EXNibReader){data.bytes,ko,vo};
        for (NSUInteger i=0; i<kc; i++) { uint32_t size=VarInt(&r); [keys addObject:UTF8(Take(&r,size),size)]; }
        End(&r); r=(EXNibReader){data.bytes,vo,co};
        for (NSUInteger i=0; i<vc; i++) {
            uint32_t key=VarInt(&r); uint8_t kind=(uint8_t)LE(&r,1); id value=nil;
            if (key>=kc) EXNibFail(@"Nib key index outside table");
            switch (kind) {
                case 0: value=@((int8_t)LE(&r,1)); break;
                case 1: value=@((int16_t)LE(&r,2)); break;
                case 2: value=@((int32_t)LE(&r,4)); break;
                case 3: value=@((int64_t)LE(&r,8)); break;
                case 4: value=@YES; break;
                case 5: value=@NO; break;
                case 6: { uint32_t bits=(uint32_t)LE(&r,4); float f; memcpy(&f,&bits,4); value=@(f); break; }
                case 7: { uint64_t bits=LE(&r,8); double d; memcpy(&d,&bits,8); value=@(d); break; }
                case 8: { uint32_t n=VarInt(&r); value=[NSData dataWithBytes:Take(&r,n) length:n]; break; }
                case 9: value=NSNull.null; break;
                case 10: { uint32_t index=(uint32_t)LE(&r,4); if (index>=oc) EXNibFail(@"Nib reference outside table"); value=@(index); break; }
                default: EXNibFail([NSString stringWithFormat:@"Unsupported nib value kind %u",kind]);
            }
            [values addObject:@{@"key":keys[key],@"kind":@(kind),@"value":value}];
        }
        End(&r); r=(EXNibReader){data.bytes,co,data.length};
        for (NSUInteger i=0; i<cc; i++) {
            uint32_t size=VarInt(&r), extras=VarInt(&r);
            if (extras>(r.limit-r.position)/4) EXNibFail(@"Invalid class extension count");
            for (NSUInteger j=0; j<extras; j++) (void)LE(&r,4);
            const uint8_t *p=Take(&r,size); if (!size || p[size-1]) EXNibFail(@"Unterminated nib class");
            [classes addObject:UTF8(p,size-1)];
        }
        End(&r); NSMutableArray *resolved=[NSMutableArray array];
        for (NSDictionary *object in objects) {
            NSUInteger cls=[object[@"class_index"] unsignedIntegerValue], start=[object[@"value_start"] unsignedIntegerValue], count=[object[@"value_count"] unsignedIntegerValue];
            if (cls>=cc || start>vc || count>vc-start) EXNibFail(@"Invalid object value range");
            [resolved addObject:@{@"class":classes[cls],@"values":[values subarrayWithRange:NSMakeRange(start,count)]}];
        }
        return @{@"format":@(v[0]),@"coder":@(v[1]),@"objects":resolved,@"classes":classes,@"keys":keys};
    } @catch (NSException *exception) { if (error) *error=EXNibError(exception); return nil; }
}

@interface EXNibConnection : NSObject
@property(nonatomic,strong) id source, destination;
@property(nonatomic,copy) NSString *label;
@end
@implementation EXNibConnection @end

@class EXNibContext;
@interface EXNibContext : NSObject
@property(nonatomic,strong) NSArray *objects;
@property(nonatomic,strong) NSMutableDictionary<NSNumber *,id> *cache;
@property(nonatomic,strong) NSMutableSet<NSNumber *> *decoding;
@property(nonatomic,strong) id owner;
@property(nonatomic,copy) EXNibObjectFactory factory;
@property(nonatomic) NSUInteger ownerIndex;
- (id)objectAt:(NSUInteger)index;
- (nullable id)valueAt:(NSUInteger)index key:(NSString *)key;
- (nullable NSDictionary *)recordAt:(NSUInteger)index key:(NSString *)key;
@end

@implementation EXNibContext
- (NSDictionary *)recordAt:(NSUInteger)index key:(NSString *)key {
    NSDictionary *found=nil;
    for (NSDictionary *v in self.objects[index][@"values"]) if ([v[@"key"] isEqual:key]) {
        if (found) EXNibFail([@"Duplicate keyed nib field: " stringByAppendingString:key]); found=v;
    }
    return found;
}
- (id)valueAt:(NSUInteger)index key:(NSString *)key {
    NSDictionary *record=[self recordAt:index key:key]; if (!record) return nil;
    if ([record[@"kind"] integerValue]==10) return [self objectAt:[record[@"value"] unsignedIntegerValue]];
    return record[@"value"]==NSNull.null ? nil : record[@"value"];
}
- (NSArray *)elementsAt:(NSUInteger)index {
    id inlined=[self valueAt:index key:@"NSInlinedValue"];
    if ([inlined boolValue]) EXNibFail(@"Inlined nib collection encoding is not implemented");
    NSMutableArray *out=[NSMutableArray array];
    for (NSDictionary *r in self.objects[index][@"values"]) if ([r[@"key"] isEqual:@"UINibEncoderEmptyKey"]) {
        if ([r[@"kind"] integerValue]!=10) EXNibFail(@"Collection member is not an object reference");
        id member=[self objectAt:[r[@"value"] unsignedIntegerValue]]; if (!member) EXNibFail(@"Nil collection member"); [out addObject:member];
    }
    return out;
}
- (id)objectAt:(NSUInteger)index {
    if (index>=self.objects.count) EXNibFail(@"Invalid nib object index");
    NSNumber *key=@(index); id cached=self.cache[key]; if (cached) return cached;
    if ([self.decoding containsObject:key]) EXNibFail(@"Unsupported cyclic immutable nib object");
    [self.decoding addObject:key]; NSDictionary *record=self.objects[index]; NSString *name=record[@"class"]; id object=nil;
    if ([name isEqual:@"NSString"]) {
        NSData *bytes=[self valueAt:index key:@"NS.bytes"];
        if (![bytes isKindOfClass:NSData.class]) EXNibFail(@"Invalid nib string bytes");
        object=[[NSString alloc] initWithData:bytes encoding:NSUTF8StringEncoding];
    } else if ([name isEqual:@"NSNumber"]) {
        object=[self valueAt:index key:@"NS.intval"];
        if (![object isKindOfClass:NSNumber.class]) EXNibFail(@"Unsupported NSNumber encoding");
    } else if ([name isEqual:@"NSArray"] || [name isEqual:@"NSMutableArray"]) {
        if ([name isEqual:@"NSMutableArray"]) { NSMutableArray *array=[NSMutableArray array]; self.cache[key]=array; [array addObjectsFromArray:[self elementsAt:index]]; object=array; }
        else object=[[self elementsAt:index] copy];
    } else if ([name isEqual:@"NSMutableSet"] || [name isEqual:@"NSSet"]) {
        object=[NSSet setWithArray:[self elementsAt:index]]; if ([name isEqual:@"NSMutableSet"]) object=[object mutableCopy];
    } else if ([name isEqual:@"IBClassReference"]) {
        object=[self valueAt:index key:@"IBClassName"];
        if (![object isKindOfClass:NSString.class]) EXNibFail(@"Invalid class reference name");
        if ([self valueAt:index key:@"IBModuleName"] || [self valueAt:index key:@"IBModuleProvider"]) EXNibFail(@"Module-qualified nib classes not implemented");
    } else if ([name isEqual:@"NSCustomObject"]) {
        NSString *className=[self valueAt:index key:@"NSClassName"];
        if (![className isKindOfClass:NSString.class]) EXNibFail(@"Custom nib object has no class name");
        id reference=[self valueAt:index key:@"IBClassReference"];
        if (reference && ![reference isKindOfClass:NSString.class]) EXNibFail(@"Invalid custom-object class reference");
        NSError *error=nil; object=self.factory(className,index==self.ownerIndex,&error);
        if (!object) EXNibFail(error.localizedDescription ?: [@"Cannot instantiate custom nib class: " stringByAppendingString:className]);
        if (index==self.ownerIndex && object!=self.owner) EXNibFail(@"Nib factory replaced the existing application owner");
    } else if ([name isEqual:@"NSNibOutletConnector"]) {
        EXNibConnection *connection=[EXNibConnection new]; self.cache[key]=connection;
        connection.source=[self valueAt:index key:@"NSSource"]; connection.destination=[self valueAt:index key:@"NSDestination"]; connection.label=[self valueAt:index key:@"NSLabel"];
        if (!connection.source || !connection.destination || ![connection.label isKindOfClass:NSString.class] || !connection.label.length) EXNibFail(@"Invalid nib outlet connection");
        if ([self valueAt:index key:@"NSChildControllerCreationSelectorName"]) EXNibFail(@"Child-controller creation not implemented"); object=connection;
    } else if ([name isEqual:@"NSIBObjectData"] || ([name isEqual:@"NSObject"] && [self recordAt:index key:@"IB.objectdata"])) {
        NSMutableDictionary *metadata=[NSMutableDictionary dictionary]; self.cache[key]=metadata;
        for (NSDictionary *value in record[@"values"]) { id v=[self valueAt:index key:value[@"key"]]; if (v) metadata[value[@"key"]]=v; } object=metadata;
    } else {
        EXNibFail([@"Unimplemented archived class: " stringByAppendingString:name]);
    }
    if (!object) EXNibFail(error.localizedDescription ?: [@"Unimplemented archived class: " stringByAppendingString:name]);
        self.cache[key]=object;
        if (![object respondsToSelector:@selector(initWithCoder:)]) EXNibFail([@"Class has no initWithCoder: " stringByAppendingString:name]);
        EXNibDecoder *decoder=[EXNibDecoder new]; decoder.context=self; decoder.index=index;
        // Factory-created instances are already initialized; invoking init again is unsafe.
        EXNibFail(@"General NSCoding class construction is not enabled for this startup decoder");
    }
    if (!object) EXNibFail([@"Failed to decode nib class: " stringByAppendingString:name]);
    self.cache[key]=object; [self.decoding removeObject:key]; return object;
}
@end

NSArray *EXNibInstantiate(NSData *data, id owner, EXNibObjectFactory factory, NSError **error) {
    NSDictionary *archive=EXNibParse(data,error); if (!archive) return nil;
    @try {
        if (!owner || !factory) EXNibFail(@"A nib owner and explicit factory are required");
        EXNibContext *context=[EXNibContext new]; context.objects=archive[@"objects"]; context.cache=[NSMutableDictionary dictionary]; context.decoding=[NSMutableSet set]; context.owner=owner; context.factory=factory;
        if (!context.objects.count) EXNibFail(@"Empty nib object table");
        NSDictionary *rootRecord=[context recordAt:0 key:@"IB.objectdata"];
        if ([rootRecord[@"kind"] integerValue]!=10) EXNibFail(@"Missing IB.objectdata reference");
        NSUInteger dataIndex=[rootRecord[@"value"] unsignedIntegerValue];
        if (dataIndex>=context.objects.count) EXNibFail(@"Invalid object-data index");
        NSDictionary *ownerRecord=[context recordAt:dataIndex key:@"NSRoot"];
        if ([ownerRecord[@"kind"] integerValue]!=10) EXNibFail(@"Missing nib root owner");
        context.ownerIndex=[ownerRecord[@"value"] unsignedIntegerValue];
        NSDictionary *objectData=[context valueAt:0 key:@"IB.objectdata"];
        if (![objectData isKindOfClass:NSDictionary.class]) EXNibFail(@"Invalid nib object-data root");
        NSArray *connections=objectData[@"NSConnections"] ?: @[];
        for (id raw in connections) {
            if (![raw isKindOfClass:EXNibConnection.class]) EXNibFail(@"Unsupported connection class");
            EXNibConnection *connection=raw; [connection.source setValue:connection.destination forKey:connection.label];
        }
        if ([objectData[@"NSAccessibilityConnectors"] count]) EXNibFail(@"Accessibility nib connections not implemented");
        if ([objectData[@"NSVisibleWindows"] count]) EXNibFail(@"Visible-window nib activation not implemented");
        NSMutableArray *top=[NSMutableArray array]; NSHashTable *seen=[NSHashTable hashTableWithOptions:NSPointerFunctionsObjectPointerPersonality];
        NSArray *archivedTop=objectData[@"NSObjectsKeys"] ?: @[];
        for (id object in [@[owner] arrayByAddingObjectsFromArray:archivedTop]) {
            if ([seen containsObject:object]) continue; [seen addObject:object];
            if (object!=owner) [top addObject:object];
            if ([object respondsToSelector:@selector(awakeFromNib)]) ((void(*)(id,SEL))objc_msgSend)(object,@selector(awakeFromNib));
        }
        return top;
    } @catch (NSException *exception) { if (error) *error=EXNibError(exception); return nil; }
}
