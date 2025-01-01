// Disable navigation when files are being uploaded to prevent uploads being canceled

const tabBarId = ''//tabBarId
const welcomeTabButtonId = ''//welcomeTabButtonId
const uploadTabButtonId = ''//uploadTabButtonId
const analyzeTabButtonId = ''//analyzeTabButtonId
const goToAnalyzeButtonId = ''//goToAnalyzeButtonId

const navigationIds = [tabBarId, welcomeTabButtonId, uploadTabButtonId, analyzeTabButtonId, goToAnalyzeButtonId];

const compareSetUploadId = ''//compareSetUploadId
const goldenSetUploadId = ''//goldenSetUploadId
const metadataUploadId = ''//metadataUploadId
const regionsUploadId = ''//regionsUploadId

const uploadIds = [compareSetUploadId, goldenSetUploadId, metadataUploadId, regionsUploadId];
const activeUploads = new Array(uploadIds.length).fill(false);

uploadListClassName = '.ant-upload-list';
const uploadListSelectors = uploadIds.map(function(id) {
    return id + ' ' + uploadListClassName;
})

let navigationDisabled = false;

const elementIds = navigationIds.concat(uploadIds)

let resizeObservers = []

let loadChecker = setInterval(function() {
    if (elementIds.every(function(element) {
        return Boolean(document.querySelector(element))
    })) {
        clearInterval(loadChecker);
        
        for (let i = 0; i < uploadListSelectors.length; i++) {
            resizeObserver = new ResizeObserver(function(entries) {
                entry = entries[0];
                activeUploads[i] = entry.contentRect.height !== 0;
                updateUploadTabNavigation();
            })
            resizeObservers.push(resizeObserver);
            resizeObserver.observe(document.querySelector(uploadListSelectors[i]));
        }
        
        new MutationObserver(function(mutations) {
            const mutation = mutations[0];
            const selectedTabClass = 'tab--selected';
            if (mutation.target.classList.contains(selectedTabClass)) {
                for (let i = 0; i < resizeObservers.length; i++) {
                    resizeObservers[i].observe(document.querySelector(uploadListSelectors[i]));
                }
            } else {
                for (let i = 0; i < resizeObservers.length; i++) {
                    resizeObservers[i].disconnect();
                }
            }
        }).observe(document.querySelector(uploadTabButtonId), {attributes: true, attributeFilter: ['class']})
    }
}, 100)

function updateUploadTabNavigation() {
    let no_active_uploads = activeUploads.every(function(condition) {
        return !condition;
    })
    
    if (no_active_uploads) {
        enableUploadTabNavigation();
    } else {
        disableUploadTabNavigation();
    }
}

function disableUploadTabNavigation() {
    if (!navigationDisabled) {
        navigationDisabled = true;
        
        document.querySelector(goToAnalyzeButtonId).disabled = true;
        document.querySelector(goToAnalyzeButtonId).style.cursor = 'not-allowed';
        
        document.querySelector(tabBarId).style.cursor = 'not-allowed';
        
        document.querySelector(welcomeTabButtonId).classList.add("tab--disabled");
        document.querySelector(welcomeTabButtonId).style.pointerEvents = 'none';
        
        document.querySelector(uploadTabButtonId).style.cursor = 'default';
        
        document.querySelector(analyzeTabButtonId).classList.add("tab--disabled");
        document.querySelector(analyzeTabButtonId).style.pointerEvents = 'none';
    }
}

function enableUploadTabNavigation() {
    if (navigationDisabled) {
        navigationDisabled = false;
        
        document.querySelector(goToAnalyzeButtonId).disabled = false;
        document.querySelector(goToAnalyzeButtonId).style.cursor = '';
        
        document.querySelector(tabBarId).style.cursor = '';
        
        document.querySelector(welcomeTabButtonId).classList.remove("tab--disabled");
        document.querySelector(welcomeTabButtonId).style.pointerEvents = '';
        
        document.querySelector(uploadTabButtonId).style.cursor = '';
        
        document.querySelector(analyzeTabButtonId).classList.remove("tab--disabled");
        document.querySelector(analyzeTabButtonId).style.pointerEvents = '';
    }
}
