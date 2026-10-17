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
        // Drawing semantics and current-context ownership are not measured yet.
        ExcelSwiftOverlayDrawingUnavailable(self, operation.rawValue)
    }
}
