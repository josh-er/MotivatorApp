import Foundation

enum PhoneFormatter {
    static func format(_ input: String) -> String {
        let digits = input.filter(\.isNumber)
        let max = String(digits.prefix(10))

        switch max.count {
        case 0...3:
            return max
        case 4...6:
            return "(\(max.prefix(3))) \(max.dropFirst(3))"
        default:
            return "(\(max.prefix(3))) \(max.dropFirst(3).prefix(3))-\(max.dropFirst(6))"
        }
    }

    static func toE164(_ input: String) -> String? {
        let digits = input.filter(\.isNumber)
        guard digits.count == 10 else { return nil }
        return "+1\(digits)"
    }
}
