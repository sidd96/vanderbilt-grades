import requests, bs4
import json
import getpass

'''
	These are all of the constants used in getting the grades
	The first three are urls, and the queries field is the maximum
	number of tries the program should try and fetch the grades if an
	error ocurred in fetching them
'''
LOGIN_URL = "https://blackboard.vanderbilt.edu/webapps/bb-auth-provider-cas-BBLEARN/execute/casLogin?cmd=login&authProviderId=_122_1&redirectUrl=https%3A%2F%2Fblackboard.vanderbilt.edu%2Fwebapps%2Fportal%2Fframeset.jsp"
GRADES_URL = "https://blackboard.vanderbilt.edu/webapps/bb-mygrades-BBLEARN/myGrades?course_id=%s&stream_name=mygrades"
STREAM_URL = "https://blackboard.vanderbilt.edu/webapps/streamViewer/streamViewer"
MAX_QUERIES = 3

'''
	This is a class used for easy text formatting in the terminal
'''
class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

'''
	Checks to see if the course is part of the current semester
	@param: the course text from the courses dictionary
	@return: boolean if course is in current sem or not
'''
def currentSem(course):
	if "2015" in course and "FALL" in course:
		return True
	return False

'''
	Gets all the grades for the course provided in the past month
	@param: the course to get grades from
	@return: a dictionary of the formatted grades in the following style

			{
				ASSIGNMENT : [GRADE, DATE DUE, DATE UPDATED, COMMENT (If included)],
				ASSIGNMENT : [GRADE, DATE DUE, DATE UPDATED, COMMENT (If included)],
				etc...
			}
'''
def getCourseGrades(course):
	soup = bs4.BeautifulSoup(course.text, "html.parser")
	gradesWrapper = soup.select(".sortable_item_row.graded_item_row.row.expanded")
	gradesDict = {}
	for item in gradesWrapper:
		item.encode("utf-8")
		assignmentGrade = item.select(".cell.grade")
		assignmentName = item.select(".cell.gradable")
		assignmentDueDate = assignmentName[0].select(".activityType")
		assignmentUpdate = item.select(".cell.activity.timestamp")

		if len(assignmentUpdate[0].select(".activityType")) != 0:
			assignmentUpdate[0].select(".activityType")[0].extract()

		if len(assignmentName[0].select(".itemCat")) != 0:
			assignmentName[0].select(".itemCat")[0].extract()

		if len(assignmentDueDate) != 0:
			assignmentDueDate[0].extract();
			assignmentDueDate[0] = assignmentDueDate[0].getText().strip()
		else:
			assignmentDueDate.append("None")

		assignmentList = [assignmentGrade[0].getText(), assignmentDueDate[0], assignmentUpdate[0].getText()]
		gradesDict[assignmentName[0].getText().strip()] = assignmentList

	return gradesDict

'''
	This function gets the formurl used to create the POST request
	in the blackboardSession
	@param: the soup object to parse
	@return: a formatted Url for the form
'''
def getFormUrl(soup):
	form = soup.select("#fm1")
	actionUrl = form[0].attrs.get("action")
	return "https://login.mis.vanderbilt.edu" + str(actionUrl)

'''
	This function gets the hidden field value for the form
	@param: soup object to parse
	@return: the hidden field 
'''
def getHiddenField(soup):
	hiddenField = soup.select("input[name]")
	return hiddenField[3].attrs.get("value")

'''
	This function returns a boolean of True if the grades were
	not found and False if they were
	@param: The response from the server
	@return: boolean of grades found or not
'''
def gradesNotFound(gradesData):
	return (len(gradesResponse["sv_extras"]["sx_filters"]) == 0)


loginPage = requests.get(LOGIN_URL)
loginPage.raise_for_status()


soup = bs4.BeautifulSoup(loginPage.text, "html.parser")

ltValue = getHiddenField(soup)
formUrl = getFormUrl(soup)

vunetUsername = input("Vunet username: ");
vunetPassword = getpass.getpass("Vunet password: ", stream = None)

formData = {
	"username" : vunetUsername, #username for blackboard
	"password" : vunetPassword, #password for blackboard
	"lt" : ltValue,
	"_eventId" : "submit",
	"submit" : "LOGIN"
}

with requests.Session() as blackboardSession:
	headers = {"User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36"}
	blackboardSession.headers.update(headers)
	loginResponse = blackboardSession.post(formUrl, data = formData)

	#yesResponse = blackboardSession.get("https://webapp.mis.vanderbilt.edu/student-search/Entry.action").text

	gradesData = {
		"cmd" : "loadStream",
		"streamName" : "mygrades",
		"providers" : {},
		"forOverview" : False
	}
	gradesResponse = json.loads(blackboardSession.post(STREAM_URL, data = gradesData).text)

	'''
		Check if the grades were found otherwise try again until found or until
		max queries limit is hit
	'''
	if gradesNotFound(gradesResponse):
		for i in range(MAX_QUERIES):
			if not gradesNotFound(gradesResponse):
				break
			gradesResponse = json.loads(blackboardSession.post(STREAM_URL, data = gradesData).text)
		raise Exception("Error fetching grades.\nPlease make sure that the username and password entered is correct.")


	courses = {}
	for courseID, courseName in gradesResponse["sv_extras"]["sx_filters"][0]["choices"].items():
		if currentSem(courseName):
			courses[courseID] = courseName

	for courseID, courseName in courses.items():
		courseGrade = blackboardSession.get(GRADES_URL % courseID)
		courseGradeDict = getCourseGrades(courseGrade) #should return a dictionary of the course grades
		print (str(len(courseGradeDict)) + " grades found for...")
		print (str(courseName) + "\n")
		for assignment, assignmentValues in  courseGradeDict.items():
			print (color.BOLD + str(assignment.strip("\t\n")) + color.END)
			print ("Grade: " + assignmentValues[0].strip("\t\n"))
			print ("Due Date: " + assignmentValues[1].strip("\t\n"))
			print ("Last Updated: " + assignmentValues[2].strip("\t\n") + "\n")


print ("Done")

