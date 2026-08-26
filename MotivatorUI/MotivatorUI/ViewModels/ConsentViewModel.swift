import Foundation
import Combine

class ConsentViewModel: ObservableObject {
    @Published var consentChecked: Bool = false
}
