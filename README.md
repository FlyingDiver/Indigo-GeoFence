Beacon
======

This plugin is based on the Beacon plugin by Fredrik Furtenbach last updated in 2016.

It has been updated for Indigo 2022.X (Python 3).  It now uses the Indigo Reflector service and
does require port forwarding to be set up.

Instead of a port number in the plugin config dialog you must provide a Reflector API key.  
See https://www.indigodomo.com/account/authorizations/ for more information.  On plugin startup,
the URL to be used in the mobile apps will be displayed.  It will look something like this:

`https://XXX.indigodomo.net/message/se.furtenbach.indigo.plugin.beacon/webhook?api_key=XXX-YYY-ZZZ-111-2345678
`

You must copy the entire URL to the mobile app.  I recommend using email, SMS, or Notes to copy it
to your devices.


| Requirement            |        |
|------------------------|--------|
| Minimum Indigo Version | 2022.1 |
| Python Library (API)   | None   |
| Requires Local Network | No     |
| Requires Internet      | Yes    |
| Hardware Interface     | None   |

The plugin has (currently) been tested with the Locative and Geofency mobile apps.  It should 
work with other apps that the original Beacon plugin supported.