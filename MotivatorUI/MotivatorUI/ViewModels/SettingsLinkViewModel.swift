import Foundation
import Combine

class SettingsLinkViewModel: ObservableObject {
    @Published var phone: String
    @Published var message: String = ""
    @Published var isLoading: Bool = false
    @Published var isError: Bool = false

    var canRequestSettingsLink: Bool { phone.filter(\.isNumber).count == 10 }

    private let client = APIClient()

    init(phone: String = "") {
        self.phone = phone
    }

    func requestSettingsLink() {
        isLoading = true
        message = ""
        isError = false

        let body = ["phone": phone]

        client.postJSON(url: APIEndpoints.requestSettingsLink, body: body) { result in
            DispatchQueue.main.async {
                self.isLoading = false

                switch result {
                case .success:
                    self.message = "If you're signed up, a settings link will be sent."
                    self.isError = false

                case .failure(let error):
                    if case APIError.httpStatus(429, _) = error {
                        self.message = "A settings link was recently sent to your phone. Please wait 30 minutes before requesting another."
                    } else {
                        self.message = "Request failed."
                    }
                    self.isError = true
                }
            }
        }
    }
}
