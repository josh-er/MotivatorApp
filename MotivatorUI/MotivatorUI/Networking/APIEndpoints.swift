import Foundation

struct APIEndpoints {
#if DEBUG
    static let baseURL = "http://127.0.0.1:5000"
#else
    static let baseURL = "https://motivatorapp.onrender.com"
#endif

    static let submit = "\(baseURL)/submit"
    static let requestSettingsLink = "\(baseURL)/request-settings-link"
}
