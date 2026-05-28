# HTML Generator

A python-based solution for the Fleet Dashboard Challenge.

---

## The Approach

Use google Gemini as AI collaborator to implement the python script that generates standalone static HTML file.

- I introduced the problem to Gemini without asking to act in persona but giving context instead. This makes sure that Gemini spends more time on becoming as expert rather than mimicking.
- The problem statement was well defined on the github repo SolidGPS/fleet-dashboard-challenge. However, I tried to make sure that Gemini could fully understand it.
- Able to catch incorrect understanding of Gemini such as using live data and backend modules.
- Made correction on Gemini understanding about the problem statement and the scope such as using vanilla.
- Gemini was instructed to not keep gnerating code without my instruction because the default response is always long.
- Keep remending Gemini about the requirements of the project that we are working on together.
- I focused on the hard part of the solution which is the map before reminding about the second and third parts of the content.
- The first generated code has syntax error, I fixed and continue the test and then the expected output has been shown.
- I observe that panning feature must be implemented to allow user navigate the map as it zooms.
- We were able to make the improvement and everything worked so far.
- Tested the output HTML file to Chrome and Edge browsers.


## Status Colour

- Using: active is green, idle is yellow, offline is dark gray, and low_battery is red.
- These colors are commonly used in mainstream consumer and enterprise applications that users get used to.


## Improvement as Real Product

- Add images of the geographic map imagery.
- Add async update of map's data and referesh on the contents.
- Add feature to plot a history (auto-refreshing or not) of geolocations of a device.
- Adaptable size of the diamond-shaped marker of each coordinate/plot based on zoom level.
- Add click event on each coordinate/plot when user clicks it and show tooltip view with all the info about the tracked item.
- Utilize AI tools that allow developer and AI to collaborate efficiently throught out the lifecycle of development such as proper versioning.

---

## Conversation with the AI collaborator

Please copy & paste the URL:
```
https://gemini.google.com/share/f45c7fd0b25e
```

