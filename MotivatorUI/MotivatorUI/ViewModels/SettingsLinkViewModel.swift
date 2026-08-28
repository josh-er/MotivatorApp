import Foundation
import Combine

class SettingsLinkViewModel: ObservableObject {
    @Published var phone: String
    @Published var message: String = ""
    @Published var isLoading: Bool = false

    private let client = APIClient()

    init(phone: String = "") {
        self.phone = phone
    }

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
                    self.message = "If you're signed up, a settings link will be sent."

                case .failure(let error):
                    if case APIError.httpStatus(429, _) = error {
                        self.message = "A settings link was recently sent to your phone. Please wait 30 minutes before requesting another."
                    } else {
                        self.message = "Request failed."
                    }
                }
            }
        }
    }
}
