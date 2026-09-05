import SwiftUI

struct ReturningUserView: View {
    @StateObject private var vm = SettingsLinkViewModel()

    var body: some View {
        VStack(spacing: 24) {
            Text("Welcome back")
                .font(.title)
                .bold()

            TextField("Phone number", text: $vm.phone)
                .textFieldStyle(.roundedBorder)
                .keyboardType(.phonePad)

            Button("Get settings link") {
                vm.requestSettingsLink()
            }
            .buttonStyle(.borderedProminent)
            .disabled(!vm.canRequestSettingsLink)

            if vm.isLoading {
                ProgressView()
            }

            Text(vm.message)
                .font(.footnote)
                .foregroundColor(.gray)

            Spacer()
        }
        .padding()
    }
}

#Preview {
    ReturningUserView()
}
