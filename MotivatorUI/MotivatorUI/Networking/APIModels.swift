import Foundation

struct SubmitRequest: Encodable {
    let phone: String
    let timezone: String
}

struct SubmitResponse: Decodable {
    let status: String
    let timezone: String
}

struct SettingsLinkRequest: Encodable {
    let phone: String
}

struct ErrorResponse: Decodable {
    let error: String
}
