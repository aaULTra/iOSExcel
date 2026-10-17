// ABI compilation probe only; do not invoke drawing without a native context.
import Foundation
import AppKit
public func excelOverlayItem(_ path: IndexPath) -> Int { path.item }
public func excelOverlayFill(_ rect: CGRect, _ operation: NSCompositingOperation) {
    rect.fill(using: operation)
}
