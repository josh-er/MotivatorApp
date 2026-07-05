import SwiftUI

struct PostSignupInfoView: View {
    var body: some View {
        VStack(spacing: 20) {
            Text("You're almost set")
                .font(.title)
                .bold()

            Text("""
Text START to the number you signed up with to activate messages.

You’ll receive one motivational text per day.
Default delivery time is 9:00 AM local.

Once activated, come back here to update your delivery time.
""")
            .multilineTextAlignment(.center)

            Spacer()
        }
        .padding()
    }
}
