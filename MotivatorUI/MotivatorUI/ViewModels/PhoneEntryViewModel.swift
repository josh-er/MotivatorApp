import Foundation
import Combine

class PhoneEntryViewModel: ObservableObject {
    let phoneNumber = PhoneNumberViewModel()
    let deliveryTime = DeliveryTimeViewModel()
    let timezone = TimezoneViewModel()
    let consent = ConsentViewModel()
    let submissionStatus = SubmissionStatusViewModel()

    var canSubmit: Bool { consent.consentChecked && timezone.timezone != nil }

    private let client = APIClient()
    private let onSignUpSuccess: (String) -> Void

    init(onSignUpSuccess: @escaping (String) -> Void = { _ in }) {
        self.onSignUpSuccess = onSignUpSuccess
    }

    // MARK: - Sign up flow (/submit)
    func signUp() {
        let phone = phoneNumber.phone

        guard !phone.isEmpty else {
            submissionStatus.message = "Phone required"
            return
        }
        guard let tz = timezone.timezone, consent.consentChecked else { return }

        submissionStatus.isLoading = true
        submissionStatus.message = ""

        let body: [String: Any] = [
            "phone": phone,
            "local_time": deliveryTime.formattedLocalTime,
            "timezone": tz,
            "consent": true,
        ]

        client.postJSON(url: APIEndpoints.submit, body: body) { result in
            DispatchQueue.main.async {
                self.submissionStatus.isLoading = false

                switch result {
                case .success:
                    UserDefaults.standard.set(true, forKey: "hasSignedUp")
                    self.onSignUpSuccess(phone)

                case .failure:
                    self.submissionStatus.message = "Sign up failed."
                }
            }
        }
    }
}
