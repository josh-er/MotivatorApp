//
//  ContentView.swift
//  MotivatorUI
//
//  Created by Josh Herz on 3/22/26.
//

import SwiftUI

struct ContentView: View {
    @AppStorage("hasSignedUp") private var hasSignedUp: Bool = false
    @State private var justSignedUpPhone: String?
    @State private var showReturningUser = false

    var body: some View {
        if let phone = justSignedUpPhone {
            PostSignupInfoView(phone: phone)
        } else if showReturningUser {
            ReturningUserView(onBack: { showReturningUser = false })
        } else if hasSignedUp {
            ReturningUserView()
        } else {
            PhoneEntryView(
                onSignUpSuccess: { phone in
                    justSignedUpPhone = phone
                },
                onRequestReturningUser: {
                    showReturningUser = true
                }
            )
        }
    }
}

#Preview {
    ContentView()
}
