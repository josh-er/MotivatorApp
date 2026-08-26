import Foundation
import Combine

class TimezoneViewModel: ObservableObject {
    @Published var timezone: String? = nil
}
