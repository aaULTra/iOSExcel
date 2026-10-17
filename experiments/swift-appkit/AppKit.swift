import Foundation
import CoreGraphics
@_exported import ExcelOverlayTypes

public extension IndexPath {
    var item: Int {
        guard count == 2 else { ExcelSwiftOverlayUnavailable("IndexPath.item requires a measured two-component path") }
        return self[1]
    }
}
public extension CGRect {
    func fill(using operation: NSCompositingOperation) {
        // Only the measured finite-rectangle copy/sourceOver subset is experimental.
        ExcelSwiftOverlayDrawingUnavailable(self, operation.rawValue)
    }
}
