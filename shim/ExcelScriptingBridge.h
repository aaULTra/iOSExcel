#pragma once
#import <Foundation/Foundation.h>
#include <sys/types.h>
// Native hierarchy and signatures measured from Mac ScriptingBridge.
// Apple-event automation is unavailable; no automation target is fabricated.
@interface SBObject : NSObject
- (instancetype)init;
@end
@interface SBApplication : SBObject
- (instancetype)init;
+ (instancetype)currentApplication;
+ (instancetype)applicationWithBundleIdentifier:(NSString *)identifier;
+ (instancetype)applicationWithProcessIdentifier:(pid_t)identifier;
@end
