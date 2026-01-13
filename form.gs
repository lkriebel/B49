// --- CONFIGURATION ---
const FIREBASE_URL = "https://timer-test-7ebe6-default-rtdb.firebaseio.com/";

// Helper function to generate the OAuth Service
function getFirebaseService() {
  const scriptProperties = PropertiesService.getScriptProperties();
  
  // NOTE: The private key in the JSON file has '\n' characters. 
  // Apps Script properties might treat them literally. We usually need to replace them.
  const privateKey = scriptProperties.getProperty('PRIVATE_KEY').replace(/\\n/g, '\n');
  const clientEmail = scriptProperties.getProperty('CLIENT_EMAIL');

  return OAuth2.createService('Firebase')
    .setTokenUrl('https://oauth2.googleapis.com/token')
    .setPrivateKey(privateKey)
    .setIssuer(clientEmail)
    .setPropertyStore(PropertiesService.getScriptProperties())
    .setScope('https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/firebase.database');
}

function onFormSubmit(e) {
  try {
    // Calculate times
    const now = new Date();
    const sheetName = e.range.getSheet().getName();

    if (sheetName !== "Sign In" && sheetName !== "Sign Out") {
      Logger.log("Bad sheet name");
      return;
    }

    const data = {
      "event": sheetName === "Sign In" ? "sign_in" : "sign_out",
      "timestamp": Math.floor((new Date().getTime()) / 1000),
    };

    if (sheetName === "Sign In") {
      Logger.log("Sign In: " + writeToFirebase(data));
    } else {
      Logger.log("Sign Out: " + writeToFirebase(data));
    }
  } catch (error) {
    Logger.log("Error in " + sheetName + ": " + error.toString());
  }
}

function writeToFirebase(data) {
  const service = getFirebaseService();
  if (!service.hasAccess()) {
    Logger.log('Authentication failed: ' + service.getLastError());
    return;
  }
  const token = service.getAccessToken();
  const url = FIREBASE_URL + "/kiosk/status.json";
  const options = {
    "method": "put",
    "contentType": "application/json",
    "headers": {
      "Authorization": "Bearer " + token,
    },
    "payload": JSON.stringify(data),
  };
  const response = UrlFetchApp.fetch(url, options);
  const code = response.getResponseCode();

  if (code !== 200) {
    throw new Error("Firebase write failed: " + response.getContentText());
  }
  return response.getContentText();
}
function testFirebaseConnection() {
  try {
    const testData = {
      "event": 'test',
      "timestamp": Math.floor((new Date().getTime()) / 1000),
    };
    
    writeToFirebase(testData);
    Logger.log('Success!\nCheck Firebase console.');
    
  } catch (error) {
    Logger.log('Error: ' + error.toString());
  }
}
// One-time Reset function (Run this manually if things break)
function resetAuth() {
  getFirebaseService().reset();
  console.log("Auth reset.");
}
