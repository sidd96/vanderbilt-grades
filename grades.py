import requests, bs4
import json

'''
	These are all of the urls used in getting the grades
'''
LOGIN_URL = "https://blackboard.vanderbilt.edu/webapps/bb-auth-provider-cas-BBLEARN/execute/casLogin?cmd=login&authProviderId=_122_1&redirectUrl=https%3A%2F%2Fblackboard.vanderbilt.edu%2Fwebapps%2Fportal%2Fframeset.jsp"
GRADES_URL = "https://blackboard.vanderbilt.edu/webapps/bb-mygrades-BBLEARN/myGrades?course_id=%s&stream_name=mygrades"
STREAM_URL = "https://blackboard.vanderbilt.edu/webapps/streamViewer/streamViewer"


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
					COURSE NAME : {
									ASSIGNMENT : [GRADE, DATE DUE, DATE UPDATED, COMMENT (If included)],
									ASSIGNMENT : [GRADE, DATE DUE, DATE UPDATED, COMMENT (If included)],
									etc...
									}
				}
'''
def getCourseGrades(course):
	soup = bs4.BeautifulSoup(course.text, "html-parser")

loginPage = requests.get(LOGIN_URL)
loginPage.raise_for_status()


soup = bs4.BeautifulSoup(loginPage.text, "html.parser")
form = soup.select("#fm1")
actionUrl = form[0].attrs.get("action")
hiddenField = soup.select("input[name]")
ltValue = hiddenField[3].attrs.get("value")

formUrl = "https://login.mis.vanderbilt.edu" + str(actionUrl)

formData = {
	"username" : "", #username for blackboard
	"password" : "", #password for blackboard
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

	
	if len(gradesResponse["sv_extras"]["sx_filters"]) == 0:
		raise Exception("Error fetching grades")


	courses = {}
	for courseID, courseName in gradesResponse["sv_extras"]["sx_filters"][0]["choices"].items():
		if currentSem(courseName):
			courses[courseID] = courseName


	print (courses)
	for courseID, courseName in courses.items():
		courseGrade = blackboardSession.get(GRADES_URL % courseID)
		courseGradeDict getCourseGrades(courseGrade) #should return a dictionary of the course grades

print ("Done")

