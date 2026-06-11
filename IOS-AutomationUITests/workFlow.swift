/*
 
 Author: 
 Creation Date:
 
 Automation for:
 
 */

import XCTest
import OSLog
import Foundation

class Workflow: XCTestCase {
    var dataLog = RunData(v1: "xctest", v2: "FAILED_TO_LAUNCH", v3: "2.3", v4: false, v5: "mm.dd.yyyy")
    
    override func tearDown() {
        //This is the last action always
        //Print runData to platform UI
        logRunData(dataLog)
        super.tearDown()
    }//tearDown.close
    
    func launchApp() -> XCUIApplication {
        
        //specify what app is getting launched/tested
        let app = XCUIApplication(bundleIdentifier: "")
        
        //set orientation
        XCUIDevice.shared.orientation = .portrait
        
        // Launches app
        app.launch()
        
        // Verifies app is running in the foreground in order to start querying elements, can lead to errors if not included
        _ = app.wait(for: .runningForeground, timeout: 30)
        
        //return app
        return(app)
        
    }//launchApp.close
    
    /*
     Helpful Function
     waitForElementToAppear(app.staticTexts.containing(NSPredicate(format: "label CONTAINS[c] 'create account'")).element(boundBy: 0), 30)
     
      Examples of utilizing Config Obj
     app.typeText(fieldsConfig?.username?.value ?? "")
     app.typeText(fieldsConfig?.password?.value ?? "")
     */
    
    func main(_ app: XCUIApplication){
        
        // For alerts
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
            
        // Credetial Config Obj
        let fieldsConfigString = ProcessInfo.processInfo.environment["NWS_FIELDS_CONFIG"] ?? "{}"
        let fieldsConfigData = fieldsConfigString.data(using: .utf8)!
        let fieldsConfig: FieldsConfig?
        do {
            fieldsConfig = try JSONDecoder().decode(FieldsConfig.self, from: fieldsConfigData)
        } catch {
            OSLog.log(message: "fieldsConfigsDecodeError:" + error.localizedDescription)
            fieldsConfig = nil
        }


        dataLog.error_code = "WORKFLOW_ERROR"
        {workflow}
        
        app.typeText(fieldsConfig?.username?.value ?? "")
        app.typeText(fieldsConfig?.password?.value ?? "")


        if !confirm_login(app, wait_interval: 1, successElements: [app.buttons["tabHomeButton"]], errorElements: [app.staticTexts["Something went wrong"]], loop_dialation: 30, dataLog: &dataLog) {
            return
        }
        dataLog.error_code = "POST_WORKFLOW_ERROR"
        
        //Post workflow actions
        {actions}
        
        //After last element is found
        dataLog.error_code = ""
        
        // Set the total expected actions for this run.
        hierarchy_loop(app, 10)
        


    }//main.close
    
    func hierarchy_loop(_ app: XCUIApplication, _ rounds: Int = 5){
        if rounds != 0 {
            app.showDebugTree()
            hierarchy_loop(app, rounds - 1)
        }
        else {
            return
        }
    }//hierarch_loop.close
}


