// Own fixture compiled against the replacement module, not Microsoft code.
import Foundation
import AppKit
if CommandLine.arguments.contains("--draw") {
    CGRect(x:1.25,y:2.5,width:20,height:30).fill(using:.sourceOver)
    fatalError("Unsupported drawing unexpectedly returned")
}
if CommandLine.arguments.contains("--invalid") {
    _ = IndexPath(indexes:[]).item
    fatalError("Unsupported empty IndexPath unexpectedly returned")
}
let pairs = [[0,0], [2,7], [11,23], [1000,999999], [0,Int.max]]
let samples: [[String: Any]] = pairs.map { ["indexes": $0, "item": IndexPath(indexes:$0).item] }
let report: [String:Any] = ["index_path_samples":samples,
    "index_path_layout":[MemoryLayout<IndexPath>.size,MemoryLayout<IndexPath>.stride,MemoryLayout<IndexPath>.alignment],
    "rect_layout":[MemoryLayout<CGRect>.size,MemoryLayout<CGRect>.stride,MemoryLayout<CGRect>.alignment],
    "operation_layout":[MemoryLayout<NSCompositingOperation>.size,MemoryLayout<NSCompositingOperation>.stride,MemoryLayout<NSCompositingOperation>.alignment],
    "drawing_executed":false,"excel_executed":false]
let data = try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys])
try data.write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
