import Foundation
import Combine

class SubmissionStatusViewModel: ObservableObject {
    @Published var message: String = ""
    @Published var isLoading: Bool = false
}
