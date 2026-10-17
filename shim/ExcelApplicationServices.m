// Original compatibility implementations; unsupported features fail explicitly.
#import "ExcelApplicationServices.h"
#import "ExcelShim.h"
#include <math.h>
#include <string.h>
static void EXUnavailable(const char *name) { ExcelShimLog([NSString stringWithFormat:@"UNAVAILABLE ApplicationServices %s; operation not performed", name]); }
__attribute__((noreturn)) static void EXServiceFault(NSString *reason) {
    ExcelShimLog(reason);
    @throw [NSException exceptionWithName:@"ExcelShimUnsupportedApplicationServices" reason:reason userInfo:nil];
}
static CGPathRef EXShapePath(HIShapeRef shape) {
    if (!shape || CFGetTypeID((CFTypeRef)shape) != CGPathGetTypeID()) EXServiceFault(@"HIShape: unknown/foreign object; only compatibility-created CGPath shapes are supported");
    return (CGPathRef)shape;
}
HIShapeRef HIShapeCreateIntersection(HIShapeRef inShape1, HIShapeRef inShape2) {
    CGPathRef a=EXShapePath(inShape1), b=EXShapePath(inShape2);
    if (CGPathIsEmpty(a) || CGPathIsEmpty(b)) return (HIShapeRef)CGPathCreateMutable();
    CGRect ra=CGRectZero, rb=CGRectZero;
    if (!CGPathIsRect(a,&ra) || !CGPathIsRect(b,&rb)) EXServiceFault(@"HIShapeCreateIntersection: nonrectangular regions are not implemented");
    // Native HIShape intersections quantize fractional rectangle regions. This
    // rule is tested against Apple's implementation, not inferred from CGPath.
    ra=CGRectIntegral(ra); rb=CGRectIntegral(rb);
    CGRect overlap=CGRectIntersection(ra,rb);
    if (CGRectIsNull(overlap) || CGRectIsEmpty(overlap)) return (HIShapeRef)CGPathCreateMutable();
    return HIShapeCreateWithRect(&overlap);
}

HIShapeRef HIShapeCreateWithRect(const CGRect * inRect) {
    if (!inRect) { ExcelShimLog(@"HIShapeCreateWithRect: NULL rectangle"); return NULL; }
    CGRect rect = *inRect;
    if (!isfinite(rect.origin.x) || !isfinite(rect.origin.y) || !isfinite(rect.size.width) || !isfinite(rect.size.height)) EXServiceFault(@"HIShapeCreateWithRect: non-finite rectangle");
    rect = CGRectStandardize(rect);
    if (!isfinite(CGRectGetMaxX(rect)) || !isfinite(CGRectGetMaxY(rect))) EXServiceFault(@"HIShapeCreateWithRect: rectangle overflow");
    if (CGRectIsEmpty(rect)) return (HIShapeRef)CGPathCreateMutable();
    return (HIShapeRef)CGPathCreateWithRect(rect, NULL);
}

Boolean HIShapeIsEmpty(HIShapeRef inShape) {
    CGPathRef path = EXShapePath(inShape);
    return (Boolean)(CGPathIsEmpty(path) || CGRectIsEmpty(CGPathGetPathBoundingBox(path)));
}

OSStatus PMCreatePageFormat(PMPageFormat * pageFormat) {
    if (pageFormat) *pageFormat = NULL; EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMCreatePrintSettings(PMPrintSettings * printSettings) {
    if (printSettings) *printSettings = NULL; EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMCreateSession(PMPrintSession * printSession) {
    if (printSession) *printSession = NULL; EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMGetAdjustedPageRect(PMPageFormat pageFormat, PMRect * pageRect) {
    if (pageRect) memset(pageRect, 0, sizeof(*pageRect)); EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMGetAdjustedPaperRect(PMPageFormat pageFormat, PMRect * paperRect) {
    if (paperRect) memset(paperRect, 0, sizeof(*paperRect)); EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMGetCollate(PMPrintSettings printSettings, Boolean * collate) {
    if (collate) *collate = 0; EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMGetCopies(PMPrintSettings printSettings, UInt32 * copies) {
    if (copies) *copies = 0; EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMGetFirstPage(PMPrintSettings printSettings, UInt32 * first) {
    if (first) *first = 0; EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMGetLastPage(PMPrintSettings printSettings, UInt32 * last) {
    if (last) *last = 0; EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMGetOrientation(PMPageFormat pageFormat, PMOrientation * orientation) {
    if (orientation) *orientation = 0; EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMPrintSettingsSetJobName(PMPrintSettings printSettings, CFStringRef name) {
     EXUnavailable(__func__); return EXPrintNotImplemented;
}

CFStringRef PMPrinterGetID(PMPrinter printer) {
    EXUnavailable(__func__); return NULL;
}

OSStatus PMPrinterGetOutputResolution(PMPrinter printer, PMPrintSettings printSettings, PMResolution * resolutionP) {
    if (resolutionP) memset(resolutionP, 0, sizeof(*resolutionP)); EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMRelease(PMObject object) {
     EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMRetain(PMObject object) {
     EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMSessionBeginCGDocumentNoDialog(PMPrintSession printSession, PMPrintSettings printSettings, PMPageFormat pageFormat) {
     EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMSessionBeginPageNoDialog(PMPrintSession printSession, PMPageFormat pageFormat, const PMRect * pageFrame) {
     EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMSessionDefaultPageFormat(PMPrintSession printSession, PMPageFormat pageFormat) {
     EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMSessionDefaultPrintSettings(PMPrintSession printSession, PMPrintSettings printSettings) {
     EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMSessionEndDocumentNoDialog(PMPrintSession printSession) {
     EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMSessionEndPageNoDialog(PMPrintSession printSession) {
     EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMSessionError(PMPrintSession printSession) {
     EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMSessionGetCGGraphicsContext(PMPrintSession printSession, CGContextRef * context) {
    if (context) *context = NULL; EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMSessionGetCurrentPrinter(PMPrintSession printSession, PMPrinter * currentPrinter) {
    if (currentPrinter) *currentPrinter = NULL; EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMSessionGetDestinationType(PMPrintSession printSession, PMPrintSettings printSettings, PMDestinationType * destTypeP) {
    if (destTypeP) *destTypeP = 0; EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMSessionSetError(PMPrintSession printSession, OSStatus printError) {
     EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PMSessionValidatePageFormat(PMPrintSession printSession, PMPageFormat pageFormat, Boolean * changed) {
    if (changed) *changed = 0; EXUnavailable(__func__); return EXPrintNotImplemented;
}

OSStatus PasteboardClear(PasteboardRef inPasteboard) {
     EXUnavailable(__func__); return EXServiceNotImplemented;
}

OSStatus PasteboardCopyItemFlavorData(PasteboardRef inPasteboard, PasteboardItemID inItem, CFStringRef inFlavorType, CFDataRef * outData) {
    if (outData) *outData = NULL; EXUnavailable(__func__); return EXServiceNotImplemented;
}

OSStatus PasteboardCopyItemFlavors(PasteboardRef inPasteboard, PasteboardItemID inItem, CFArrayRef * outFlavorTypes) {
    if (outFlavorTypes) *outFlavorTypes = NULL; EXUnavailable(__func__); return EXServiceNotImplemented;
}

OSStatus PasteboardCreate(CFStringRef inName, PasteboardRef * outPasteboard) {
    if (outPasteboard) *outPasteboard = NULL; EXUnavailable(__func__); return EXServiceNotImplemented;
}

OSStatus PasteboardGetItemCount(PasteboardRef inPasteboard, EXDesktopItemCount * outItemCount) {
    if (outItemCount) *outItemCount = 0; EXUnavailable(__func__); return EXServiceNotImplemented;
}

OSStatus PasteboardGetItemIdentifier(PasteboardRef inPasteboard, CFIndex inIndex, PasteboardItemID * outItem) {
    if (outItem) *outItem = NULL; EXUnavailable(__func__); return EXServiceNotImplemented;
}

OSStatus PasteboardPutItemFlavor(PasteboardRef inPasteboard, PasteboardItemID inItem, CFStringRef inFlavorType, CFDataRef inData, PasteboardFlavorFlags inFlags) {
     EXUnavailable(__func__); return EXServiceNotImplemented;
}

PasteboardSyncFlags PasteboardSynchronize(PasteboardRef inPasteboard) {
    EXServiceFault(@"PasteboardSynchronize: pasteboard adapter not implemented; no flags fabricated");
}

OSStatus UAZoomChangeFocus(const CGRect * inRect, const CGRect * inHighlightRect, UAZoomChangeFocusType inType) {
    EXUnavailable(__func__); return EXServiceNotImplemented;
}

Boolean UAZoomEnabled(void) {
    // The macOS zoom compatibility feature is disabled. This is not a query of
    // the iPad's accessibility settings; no verified UIKit status API is assumed.
    EXUnavailable(__func__); return (Boolean)0;
}
