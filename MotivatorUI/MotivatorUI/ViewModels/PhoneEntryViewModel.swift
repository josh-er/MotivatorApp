import Foundation
import Combine

class PhoneEntryViewModel: ObservableObject {
    @Published var phone: String = ""
    @Published var selectedTime: Date = Date()
    @Published var timezone: String? = nil
    @Published var consentChecked: Bool = false
    @Published var message: String = ""
    @Published var isLoading: Bool = false

    var canSubmit: Bool { consentChecked && timezone != nil }

    private let client = APIClient()

    // MARK: - Sign up flow (/submit)
    func signUp() {
        guard !phone.isEmpty else {
            message = "Phone required"
            return
        }
        guard let tz = timezone, consentChecked else { return }

        isLoading = true
        message = ""

        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        let localTime = formatter.string(from: selectedTime)

        let body: [String: Any] = [
            "phone": phone,
            "local_time": localTime,
            "timezone": tz,
            "consent": true,
        ]

        client.postJSON(url: APIEndpoints.submit, body: body) { result in
            DispatchQueue.main.async {
                self.isLoading = false

                switch result {
                case .success:
                    self.message = "Text START to activate. Then return to request your settings link."

                case .failure:
                    self.message = "Sign up failed."
                }
            }
        }
    }

    // MARK: - Settings link flow (/request-settings-link)
    func requestSettingsLink() {
        guard !phone.isEmpty else {
            message = "Phone required"
            return
        }

        isLoading = true
        message = ""

        let body = ["phone": phone]

        client.postJSON(url: APIEndpoints.requestSettingsLink, body: body) { result in
            DispatchQueue.main.async {
                self.isLoading = false

                switch result {
                case .success:
                    self.message = "If START was texted, a settings link will be sent."

                case .failure:
                    self.message = "Request failed."
                }
            }
        }
    }
}
