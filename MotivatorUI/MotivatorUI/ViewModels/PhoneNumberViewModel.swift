import Foundation
import Combine

class PhoneNumberViewModel: ObservableObject {
    @Published var phone: String = ""
}
