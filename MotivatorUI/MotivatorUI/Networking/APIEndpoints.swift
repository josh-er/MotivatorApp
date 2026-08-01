import Foundation

struct APIEndpoints {
#if DEBUG
    static let baseURL = "https://motivatorapp.onrender.com"
#else
    static let baseURL = "https://motivatorapp.onrender.com"
#endif

    static let submit = "\(baseURL)/submit"
    static let requestSettingsLink = "\(baseURL)/request-settings-link"
}
