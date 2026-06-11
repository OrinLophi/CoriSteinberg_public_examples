// Key NowSecure Extensions and functionality.

import XCTest
import os.log
import XCTest
import UIKit
import Foundation

struct RunData: Codable {
    var navigation_type: String
    var error_code: String
    var rundata_version: String
    var login_success: Bool
    var date_written: String


    init(v1: String, v2: String, v3: String, v4: Bool, v5: String) {
        navigation_type = v1
        error_code = v2
        rundata_version = v3
        login_success = v4
        date_written = v5
    }
}


struct Field: Codable {
    var value: String
}
struct FieldsConfig: Codable {
    var username: Field?
    var name: Field?
    var firstname: Field?
    var lastname: Field?
    var phonenumber: Field?
    var email: Field?
    var password: Field?
    var zipcode: Field?
    var search_terms_0: Field?
}

func logRunData(_ object: RunData){
    do {
        let jsonData = try JSONEncoder().encode(object)
        let jsonString = String(data: jsonData, encoding: .utf8)!
        print("\n\n")
        print("runData:" + jsonString)
        OSLog.log(message: "runData:" + jsonString)
    } catch { OSLog.log(message: "runData error = " + error.localizedDescription) }
}

// for Swift 4 you need to add the constrain `where Index == String.Index`
extension StringProtocol {
    var byWords: [SubSequence] {
        var byWords: [SubSequence] = []
        enumerateSubstrings(in: startIndex..., options: .byWords) { _, range, _, _ in
            byWords.append(self[range])
        }
        return byWords
    }
}

extension UIDevice {
    var modelName: String {
        var systemInfo = utsname()
        uname(&systemInfo)
        let machineMirror = Mirror(reflecting: systemInfo.machine)
        let identifier = machineMirror.children.reduce("") { identifier, element in
            guard let value = element.value as? Int8, value != 0 else { return identifier }
            return identifier + String(UnicodeScalar(UInt8(value)))
        }
        return identifier
    }
}

extension OSLog {
    private static var subsystem = Bundle.main.bundleIdentifier ?? "XCUITest"
    static let loginActivity = OSLog(subsystem: subsystem, category: "login")
    static let runnerActivity = OSLog(subsystem: subsystem, category: "xctest-script")
    static func loginAttempted() {
        os_log("attempted", log: OSLog.loginActivity, type: .info)
    }
    static func loginFailed() {
        os_log("failed", log: OSLog.loginActivity, type: .info)
    }
    static func logSS(message: StaticString) {
        os_log(message, log: OSLog.runnerActivity, type: .info)
    }
    static func log(message: String) {
        os_log("%{public}s", log: OSLog.runnerActivity, type: .info, message)
    }
}

extension XCUIElement {
    // To be used if two elements are close to or overlap each other.
    // Clicks the center of the element
    func forceTap() {
        if self.isHittable {
            self.tap()
        }
        else {
            coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
        }
    }
}

extension XCUIApplication {
    /*
         Uses floating vector variables to coordinate point on screen.
         To be used when CGPoints cannot be found or an element
         doesn't show in the UI heirarchy
     */
    func tapByVector(_ dxv: Double,_ dyv: Double){
        coordinate(withNormalizedOffset: CGVector(dx: dxv, dy: dyv)).tap()
    }
    
    /*
         To use:
         let point = CGPoint(x: 731, y: 268)
         app.tapCoordinate(at: point)
     */
    func tapCoordinate(at point: CGPoint) {
        let normalized = coordinate(withNormalizedOffset: .zero)
        let offset = CGVector(dx: point.x, dy: point.y)
        let coordinate = normalized.withOffset(offset)
        coordinate.tap()
    }
    
    /*
         Function to print debug tree
         To call - use - app.showDebugTree()
     */
    func showDebugTree() {
        print("\n\nTree Start\n\n" + debugDescription + "\n\nTree End\n\n")
    }
}

extension XCTestCase {
    
    // Utilize for dyamically waiting for elements.
    func waitForElementToAppear(_ element: XCUIElement, _ timeout: TimeInterval) {
        let existsPredicate = NSPredicate(format: "exists == true")
        expectation(for: existsPredicate, evaluatedWith: element, handler: nil)
        waitForExpectations(timeout: timeout, handler: nil)
    }
    
    // This ensures that the screenshot is retained
    func takeScreenshot(_ app: XCUIApplication) {
        let finalScreenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: finalScreenshot);
        add(attachment);
    }
    /*
     This can be used in place of sleep() and will wait without blocking the
     thread.  Normally an expectation like this would fail, but by setting
     isInverted = true we indicate that we expect failure.  This prevents
     the test from failing when the timeout hits.
     https://developer.apple.com/documentation/xctest/xctestexpectation/2806573-inverted?language=objc
     */
    func arbitraryWait(_ timeout: TimeInterval) {
        let delayExpectation = XCTestExpectation()
        delayExpectation.isInverted = true
        wait(for: [delayExpectation], timeout: timeout)
    }
    func secondary_success_validation(_ app: XCUIApplication) -> Bool{
        let success_terms = ["Home", "Account", "Messages", "Profile", "Logout", "Settings", "Log out"]
        
        for term in success_terms {
            if app.staticTexts.containing(NSPredicate(format: "label CONTAINS[c] '\(term)'")).element(boundBy: 0).exists || app.buttons.containing(NSPredicate(format: "label CONTAINS[c] '\(term)'")).element(boundBy: 0).exists {
                return true
            }
        }
         if app.navigationBars.element(boundBy: 0).exists { return true }
        //if we reach this point nothing was found
        return false
    }
    
    func secondary_failure_validation(_ app: XCUIApplication) -> Bool{
        let error_terms = ["Invalid", "Please enter a valid", "error", "try again", "incorrect", "failed"]
        
        for term in error_terms {
            if app.staticTexts.containing(NSPredicate(format: "label CONTAINS[c] '\(term)'")).element(boundBy: 0).exists || app.buttons.containing(NSPredicate(format: "label CONTAINS[c] '\(term)'")).element(boundBy: 0).exists {
                return true
            }
        }
        if app.alerts.element(boundBy: 0).exists { return true }
        //if we reach this point nothing was found
        return false
    }
    
    // Confirmation Login function draft.
    func confirm_login(_ app: XCUIApplication, wait_interval: TimeInterval = 1, successElements: [XCUIElement] = [], errorElements: [XCUIElement] = [], loop_dialation: Int = 30, dataLog: inout RunData) -> Bool {
        
        
        for _ in (0...loop_dialation){
            
            for element in successElements {
                if element.exists {
                    dataLog.login_success = true
                    dataLog.error_code = ""
                    return true
                }
            }
            for errors in errorElements {
                if errors.exists {
                    dataLog.error_code = "ERROR_ELEMENT_FOUND"
                    return false
                }
            }
            arbitraryWait(wait_interval)
        }

        if secondary_failure_validation(app){
            dataLog.login_success = false
            dataLog.error_code = "SUBMISSION_FAILURE"
            return false
        }
        else if secondary_success_validation(app){
            dataLog.login_success = true
            dataLog.error_code = ""
            return true
        }
        else if app.secureTextFields.element(boundBy: 0).exists {
            dataLog.login_success = false
            dataLog.error_code = "SUBMISSION_FAILURE"
            return false
            
        }
        else{
            dataLog.login_success = false
            dataLog.error_code = "LOGIN_UNKNOWN"
            return false
        }
    }
    
}//ext.UITest.close

//Main Class
class appAutomation: Workflow {
    static var swizzledOutIdle = false
       override func setUp() {
           if !appAutomation.swizzledOutIdle { // ensure the swizzle only happens once
               let replaced = class_getInstanceMethod(type(of: self), #selector(appAutomation.replace))
               if let original = class_getInstanceMethod((objc_getClass("XCUIApplicationProcess") as? AnyClass), Selector(("waitForQuiescenceIncludingAnimationsIdle:usingActivity:isPreEvent:"))) {
                       method_exchangeImplementations(original, replaced!)
               }//if(original).close
               
               appAutomation.swizzledOutIdle = true
               
           }//if.swizzleOutIdle.close
           
           // uncomment this if the app uses WKWebView
           //workaroundWKWebView()
           super.setUp()
       }//setup.close
    
    @objc func replace() {
        return
    }
    
    //Main Test Functionality
    func testExample() {
        //Launch app function in workflow.swift
        let app = launchApp()
        OSLog.log(message: "RunData Present in Script")
        //Call to main function in workFlow.swift
        main(app)
    }//testExample.close
}//class.close
