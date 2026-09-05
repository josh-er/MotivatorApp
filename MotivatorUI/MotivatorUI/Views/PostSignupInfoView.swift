import SwiftUI

struct PostSignupInfoView: View {
    @StateObject private var settingsVM: SettingsLinkViewModel

    init(phone: String) {
        _settingsVM = StateObject(wrappedValue: SettingsLinkViewModel(phone: phone))
    }

    var body: some View {
        VStack(spacing: 24) {
            Image("AppLogo")
                .resizable()
                .scaledToFit()
                .frame(height: 60)
                .frame(maxWidth: .infinity, alignment: .center)
                .padding(.top, 24)

            VStack(spacing: 12) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.largeTitle)
                    .foregroundColor(.successGreen)

                Text("You're signed up.")
                    .font(.title2)
                    .bold()
                    .foregroundColor(.textPrimary)

                Text("Check your phone for a confirmation text.")
                    .multilineTextAlignment(.center)
                    .foregroundColor(.textSecondary)
            }
            .padding()

            VStack(spacing: 12) {
                Text("Need to update your settings?")
                    .font(.headline)
                    .foregroundColor(.textPrimary)

                TextField("Phone number", text: $settingsVM.phone)
                    .foregroundColor(.textPrimary)
                    .inputBordered()
                    .keyboardType(.phonePad)

                Button("Get settings link") {
                    settingsVM.requestSettingsLink()
                }
                .buttonStyle(PrimaryButtonStyle())
                .disabled(!settingsVM.canRequestSettingsLink)

                if settingsVM.isLoading {
                    ProgressView()
                }

                Text(settingsVM.message)
                    .font(.footnote)
                    .foregroundColor(settingsVM.isError ? .errorText : .textSecondary)
                    .padding(settingsVM.isError ? 8 : 0)
                    .background(settingsVM.isError ? Color.errorBackground : Color.clear)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(settingsVM.isError ? Color.errorBorder : Color.clear, lineWidth: 1)
                    )
            }
            .padding()
            .background(Color.elevatedSurface)
            .cornerRadius(12)

            Spacer()
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.appBackground.ignoresSafeArea())
    }
}

#Preview {
    PostSignupInfoView(phone: "+15551234567")
}
