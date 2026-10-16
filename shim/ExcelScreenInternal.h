#import "ExcelScreen.h"
NS_ASSUME_NONNULL_BEGIN
// Internal provider boundary; native tests supply synthetic metrics without UIKit.
@protocol EXScreenMetricsProvider <NSObject>
@property(nonatomic,readonly) BOOL available;
@property(nonatomic,readonly) CGRect bounds;
@property(nonatomic,readonly) CGRect usableBounds;
@property(nonatomic,readonly) CGFloat backingScale;
@property(nonatomic,readonly,copy) NSString *workspaceName;
@end
FOUNDATION_EXPORT void EXScreenSetProvider(id<EXScreenMetricsProvider> _Nullable provider);
NS_ASSUME_NONNULL_END
