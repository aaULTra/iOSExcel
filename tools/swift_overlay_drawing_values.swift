// Native offscreen behavior probe. No windows, Office resources or account APIs.
import Foundation
import AppKit
#if EXCEL_OVERLAY_DRAWING_TEST && !os(macOS)
import UIKit
#endif
let rectangles = [CGRect(x:1,y:1,width:4,height:4), CGRect(x:1.25,y:2.5,width:4.5,height:3.25),
    CGRect(x:-1,y:-1,width:4,height:4), CGRect(x:3,y:1,width:0,height:4),
    CGRect(x:5,y:5,width:-3,height:-2), CGRect(x:0,y:0,width:12,height:8)]
let operations: [NSCompositingOperation] = [.copy,.sourceOver]
var records: [[String:Any]] = []
for (index,rect) in rectangles.enumerated() {
  for operation in operations {
    for flipped in [false,true] {
      for transformed in [false,true] {
        for multiply in [false,true] {
          var bytes = [UInt8](repeating:0,count:12*8*4)
          var finalTransform: [Double] = []
          bytes.withUnsafeMutableBytes { memory in
            let space = CGColorSpace(name:CGColorSpace.sRGB)!
            let context = CGContext(data:memory.baseAddress,width:12,height:8,bitsPerComponent:8,bytesPerRow:48,
                space:space,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue | CGBitmapInfo.byteOrder32Big.rawValue)!
            context.setAllowsAntialiasing(false)
            context.setFillColor(red:0.1,green:0.2,blue:0.7,alpha:0.8)
            context.fill(CGRect(x:0,y:0,width:12,height:8))
            if transformed { context.translateBy(x:1,y:1); context.scaleBy(x:0.75,y:0.75) }
#if EXCEL_OVERLAY_DRAWING_TEST
#if os(macOS)
            ExcelSwiftOverlaySetTestContext(context)
#else
            UIGraphicsPushContext(context)
#endif
#else
            let previous = NSGraphicsContext.current
            NSGraphicsContext.current = NSGraphicsContext(cgContext:context,flipped:flipped)
#endif
            context.setBlendMode(multiply ? .multiply : .normal)
            context.setFillColor(red:0.8,green:0.2,blue:0.1,alpha:0.5)
            rect.fill(using:operation)
            // Disjoint follow-up fills expose persistent blend/fill/transform state.
            context.fill(CGRect(x:9,y:1,width:1,height:1))
            context.setFillColor(red:0.2,green:0.8,blue:0.3,alpha:0.6)
            context.fill(CGRect(x:10,y:2,width:1,height:1))
            context.flush()
            let m = context.ctm
            finalTransform = [Double(m.a),Double(m.b),Double(m.c),Double(m.d),Double(m.tx),Double(m.ty)]
#if EXCEL_OVERLAY_DRAWING_TEST
#if os(macOS)
            ExcelSwiftOverlaySetTestContext(nil)
#else
            UIGraphicsPopContext()
#endif
#else
            NSGraphicsContext.current = previous
#endif
          }
          records.append(["rect_index":index,"operation":operation.rawValue,"flipped":flipped,
              "transformed":transformed,"preexisting_multiply":multiply,"rgba_base64":Data(bytes).base64EncodedString(),
              "ctm_after":finalTransform])
        }
      }
    }
  }
}
#if EXCEL_OVERLAY_DRAWING_TEST
let nativeAppKit = false
#else
let nativeAppKit = true
#endif
let report:[String:Any] = ["cases":records,"width":12,"height":8,"color_space":"sRGB",
    "antialiasing":false,"native_appkit_drawing_executed":nativeAppKit,"excel_executed":false,
    "scope":"Two explicit operations, six finite rectangles, context transforms/flipped flags and follow-up state observers only"]
let data = try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys])
try data.write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
