// Desktop C ABI compatibility. Types measured from the arm64 Mac SDK.
#pragma once
#import <CoreFoundation/CoreFoundation.h>
#import <CoreGraphics/CoreGraphics.h>
#import <TargetConditionals.h>
#include <stdint.h>
typedef unsigned long EXDesktopItemCount;
enum { EXServiceNotImplemented = -4, EXServiceParamError = -50, EXPrintNotImplemented = -30873 };
#if TARGET_OS_OSX && !defined(EXCELSHIM_SERVICE_TYPES_ONLY)
#import <ApplicationServices/ApplicationServices.h>
#else
typedef struct OpaquePMPrinter *PMPrinter;
typedef struct OpaquePMPageFormat *PMPageFormat;
typedef struct OpaquePMPrintSession *PMPrintSession;
typedef struct OpaquePMPrintSettings *PMPrintSettings;
typedef const void *PMObject;
typedef uint16_t PMOrientation;
typedef uint16_t PMDestinationType;
typedef struct PMRect { double top, left, bottom, right; } PMRect;
typedef struct PMResolution { double hRes, vRes; } PMResolution;
typedef struct OpaquePasteboardRef *PasteboardRef;
typedef void *PasteboardItemID;
typedef uint32_t PasteboardSyncFlags;
typedef uint32_t PasteboardFlavorFlags;
typedef const struct __HIShape *HIShapeRef;
typedef uint32_t UAZoomChangeFocusType;
HIShapeRef HIShapeCreateIntersection(HIShapeRef inShape1, HIShapeRef inShape2);
HIShapeRef HIShapeCreateWithRect(const CGRect * inRect);
Boolean HIShapeIsEmpty(HIShapeRef inShape);
OSStatus PMCreatePageFormat(PMPageFormat * pageFormat);
OSStatus PMCreatePrintSettings(PMPrintSettings * printSettings);
OSStatus PMCreateSession(PMPrintSession * printSession);
OSStatus PMGetAdjustedPageRect(PMPageFormat pageFormat, PMRect * pageRect);
OSStatus PMGetAdjustedPaperRect(PMPageFormat pageFormat, PMRect * paperRect);
OSStatus PMGetCollate(PMPrintSettings printSettings, Boolean * collate);
OSStatus PMGetCopies(PMPrintSettings printSettings, UInt32 * copies);
OSStatus PMGetFirstPage(PMPrintSettings printSettings, UInt32 * first);
OSStatus PMGetLastPage(PMPrintSettings printSettings, UInt32 * last);
OSStatus PMGetOrientation(PMPageFormat pageFormat, PMOrientation * orientation);
OSStatus PMPrintSettingsSetJobName(PMPrintSettings printSettings, CFStringRef name);
CFStringRef PMPrinterGetID(PMPrinter printer);
OSStatus PMPrinterGetOutputResolution(PMPrinter printer, PMPrintSettings printSettings, PMResolution * resolutionP);
OSStatus PMRelease(PMObject object);
OSStatus PMRetain(PMObject object);
OSStatus PMSessionBeginCGDocumentNoDialog(PMPrintSession printSession, PMPrintSettings printSettings, PMPageFormat pageFormat);
OSStatus PMSessionBeginPageNoDialog(PMPrintSession printSession, PMPageFormat pageFormat, const PMRect * pageFrame);
OSStatus PMSessionDefaultPageFormat(PMPrintSession printSession, PMPageFormat pageFormat);
OSStatus PMSessionDefaultPrintSettings(PMPrintSession printSession, PMPrintSettings printSettings);
OSStatus PMSessionEndDocumentNoDialog(PMPrintSession printSession);
OSStatus PMSessionEndPageNoDialog(PMPrintSession printSession);
OSStatus PMSessionError(PMPrintSession printSession);
OSStatus PMSessionGetCGGraphicsContext(PMPrintSession printSession, CGContextRef * context);
OSStatus PMSessionGetCurrentPrinter(PMPrintSession printSession, PMPrinter * currentPrinter);
OSStatus PMSessionGetDestinationType(PMPrintSession printSession, PMPrintSettings printSettings, PMDestinationType * destTypeP);
OSStatus PMSessionSetError(PMPrintSession printSession, OSStatus printError);
OSStatus PMSessionValidatePageFormat(PMPrintSession printSession, PMPageFormat pageFormat, Boolean * changed);
OSStatus PasteboardClear(PasteboardRef inPasteboard);
OSStatus PasteboardCopyItemFlavorData(PasteboardRef inPasteboard, PasteboardItemID inItem, CFStringRef inFlavorType, CFDataRef * outData);
OSStatus PasteboardCopyItemFlavors(PasteboardRef inPasteboard, PasteboardItemID inItem, CFArrayRef * outFlavorTypes);
OSStatus PasteboardCreate(CFStringRef inName, PasteboardRef * outPasteboard);
OSStatus PasteboardGetItemCount(PasteboardRef inPasteboard, EXDesktopItemCount * outItemCount);
OSStatus PasteboardGetItemIdentifier(PasteboardRef inPasteboard, CFIndex inIndex, PasteboardItemID * outItem);
OSStatus PasteboardPutItemFlavor(PasteboardRef inPasteboard, PasteboardItemID inItem, CFStringRef inFlavorType, CFDataRef inData, PasteboardFlavorFlags inFlags);
PasteboardSyncFlags PasteboardSynchronize(PasteboardRef inPasteboard);
OSStatus UAZoomChangeFocus(const CGRect * inRect, const CGRect * inHighlightRect, UAZoomChangeFocusType inType);
Boolean UAZoomEnabled(void);
#endif
