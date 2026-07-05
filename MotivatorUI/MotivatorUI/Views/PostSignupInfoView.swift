import SwiftUI

struct PostSignupInfoView: View {
    @StateObject private var settingsVM: SettingsLinkViewModel

    init(phone: String) {
        _settingsVM = StateObject(wrappedValue: SettingsLinkViewModel(phone: phone))
    }

    var body: some View {
        VStack(spacing: 24) {
            VStack(spacing: 12) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.largeTitle)
                    .foregroundColor(.green)

                Text("You're signed up.")
                    .font(.title2)
                    .bold()

                Text("Check your phone for a confirmation text.")
                    .multilineTextAlignment(.center)
                    .foregroundColor(.secondary)
            }
            .padding()

            VStack(spacing: 12) {
                Text("Need to update your settings?")
                    .font(.headline)

                TextField("Phone number", text: $settingsVM.phone)
                    .textFieldStyle(.roundedBorder)
                    .keyboardType(.phonePad)

                Button("Get settings link") {
                    settingsVM.requestSettingsLink()
                }
                .buttonStyle(.bordered)

                if settingsVM.isLoading {
                    ProgressView()
                }

                Text(settingsVM.message)
                    .font(.footnote)
                    .foregroundColor(.gray)
            }
            .padding()
            .background(Color(.secondarySystemBackground))
            .cornerRadius(12)

            Spacer()
        }
        .padding()
    }
}

#Preview {
    PostSignupInfoView(phone: "+15551234567")
}
