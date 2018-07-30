from django.http import HttpResponse

def home(request):
    msg = """
    <head>
    <title>SLCPython</title>
    </head>
    <body>
    <p>
    Howdy SLCPythoners. We're re-constructing the site to be more robust and
    devops-friendly. Please check back in mid-August 2018.
    </p>

    <p>
    Until then, please visit our main meetup site:
    <a href="https://meetup.com/SLCPython">meetup.com/SLCPython</a>
    </p>
    </body>
    """
    return HttpResponse(msg)

