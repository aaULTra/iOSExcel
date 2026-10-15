#import <Foundation/Foundation.h>
NS_ASSUME_NONNULL_BEGIN
// The factory resolves archived custom objects. It must fail rather than fabricate classes.
typedef id _Nullable (^EXNibObjectFactory)(NSString *className, BOOL isOwner, NSError **error);
FOUNDATION_EXPORT NSDictionary * _Nullable EXNibParse(NSData *data, NSError **error);
// Supports the observed startup graph, not arbitrary AppKit controls or nib archives.
FOUNDATION_EXPORT NSArray * _Nullable EXNibInstantiate(NSData *data, id owner,
    EXNibObjectFactory factory, NSError **error);
NS_ASSUME_NONNULL_END
