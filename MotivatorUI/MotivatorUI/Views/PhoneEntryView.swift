import SwiftUI

private let supportedTimezones: [(id: String, label: String)] = [
    ("America/New_York",             "Eastern (New York)"),
    ("America/Chicago",              "Central (Chicago)"),
    ("America/Denver",               "Mountain (Denver)"),
    ("America/Phoenix",              "Mountain \u{2013} no DST (Phoenix)"),
    ("America/Los_Angeles",          "Pacific (Los Angeles)"),
    ("America/Anchorage",            "Alaska (Anchorage)"),
    ("America/Nome",                 "Alaska (Nome)"),
    ("America/Juneau",               "Alaska (Juneau)"),
    ("Pacific/Honolulu",             "Hawaii \u{2013} no DST (Honolulu)"),
    ("America/Adak",                 "Hawaii-Aleutian (Adak)"),
    ("America/Indiana/Indianapolis", "Eastern \u{2013} no DST (Indianapolis)"),
    ("America/Boise",                "Mountain (Boise)"),
]

struct PhoneEntryView: View {
    @StateObject var vm: PhoneEntryViewModel

    init(onSignUpSuccess: @escaping (String) -> Void = { _ in }) {
        _vm = StateObject(wrappedValue: PhoneEntryViewModel(onSignUpSuccess: onSignUpSuccess))
    }

    var body: some View {
        VStack(spacing: 24) {

            TextField("Phone number", text: $vm.phone)
                .textFieldStyle(.roundedBorder)
                .keyboardType(.phonePad)

            DatePicker(
                "Delivery time",
                selection: $vm.selectedTime,
                displayedComponents: .hourAndMinute
            )
            .datePickerStyle(.compact)

            Picker(selection: $vm.timezone) {
                Text("Select timezone").tag(String?.none)
                ForEach(supportedTimezones, id: \.id) { tz in
                    Text(tz.label).tag(Optional(tz.id))
                }
            } label: {
                Text("Timezone")
            }
            .pickerStyle(.menu)

            ConsentCheckbox(isChecked: $vm.consentChecked)

            Button("Sign up") {
                vm.signUp()
            }
            .buttonStyle(.borderedProminent)
            .disabled(!vm.canSubmit)

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

private struct ConsentCheckbox: View {
    @Binding var isChecked: Bool

    var body: some View {
        Button(action: { isChecked.toggle() }) {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: isChecked ? "checkmark.square.fill" : "square")
                    .foregroundColor(isChecked ? .accentColor : .secondary)
                    .imageScale(.large)
                Text("By checking this box, I agree to receive recurring automated motivational SMS messages. Msg & data rates may apply. Reply STOP to cancel.")
                    .font(.footnote)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.leading)
            }
        }
        .buttonStyle(.plain)
    }
}
