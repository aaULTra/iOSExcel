// Native values only. No windows, drawing, automation or Office execution.
import Foundation
import AppKit
let pairs = [[0,0], [2,7], [11,23], [1000,999999], [0,Int.max]]
let rows: [[String: Any]] = pairs.map { ["indexes": $0, "item": IndexPath(indexes: $0).item] }
let report: [String: Any] = ["index_path_samples": rows,
    "index_path_layout": [MemoryLayout<IndexPath>.size, MemoryLayout<IndexPath>.stride, MemoryLayout<IndexPath>.alignment],
    "rect_layout": [MemoryLayout<CGRect>.size, MemoryLayout<CGRect>.stride, MemoryLayout<CGRect>.alignment],
    "operation_layout": [MemoryLayout<NSCompositingOperation>.size, MemoryLayout<NSCompositingOperation>.stride, MemoryLayout<NSCompositingOperation>.alignment],
    "drawing_executed": false, "excel_executed": false, "authentication_attempted": false]
let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
try data.write(to: URL(fileURLWithPath: CommandLine.arguments[1]))
