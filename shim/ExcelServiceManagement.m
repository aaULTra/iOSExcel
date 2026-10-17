#ifdef EXCELSHIM_SERVICE_NATIVE_DECLARATIONS
#import <ServiceManagement/ServiceManagement.h>
#else
#import "ExcelServiceManagement.h"
#endif
#import "ExcelShim.h"
// Exact native constant value measured in run 39022987157.
CFStringRef const kSMDomainUserLaunchd = CFSTR("kSMDomainUserLaunchd");
CFArrayRef SMCopyAllJobDictionaries(CFStringRef domain) {
    (void)domain;
    ExcelShimLog(@"ServiceManagement job enumeration unavailable: returning documented NULL error, not an empty job list or a fabricated service");
    return NULL;
}
