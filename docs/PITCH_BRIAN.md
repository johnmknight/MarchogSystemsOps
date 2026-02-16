# Marchog Systems — Pitch for Brian (The Smugglers Room)

---

## Hey Brian,

I've been building a themed room of my own, and one problem I kept hitting was the screens. You know the ones — those small displays embedded in panels, consoles, doorways. The ones that make the space feel *alive*.

Right now, most of us are doing the same thing: cheap digital media players looping MP4s on a USB stick. You can flip between loaded videos with an IR remote, which works fine day-to-day. But there are limits:

- Want to add new content or swap out old clips? That means physical access — pulling the USB, loading files on a computer, plugging it back in. For screens buried behind panels, that's not a quick task.
- Want all your screens to change at the same time — like triggering an alert mode or a dramatic scene shift? You'd need a remote for every player and the hands of Dexter Jettster to pull it off.
- Want a screen to show something dynamic, like a real-time animated display or a procedural effect? A media player can only loop files — it can't run anything interactive.
- Want to manage everything from your phone or another room? IR remotes need line of sight to each individual player.

---

## What Marchog Systems Does

Marchog Systems is a free, open-source screen controller I've been building specifically for themed room builds. Instead of standalone media players, each screen connects to a small server (a Raspberry Pi or any old laptop) running on your local WiFi. Every screen just opens a web browser — that's it.

From one control page, you can:

**See every screen in your room at a glance.** Which ones are online, what they're displaying, where they are. You define the rooms and zones — a bar area, a doorway, a cockpit bench, whatever your build has.

**Assign any content to any screen instantly.** Video loops, animated displays, standby screens — point and click. No USB swapping, no walking around the room.

**Create video pages with custom borders.** Take any video (YouTube link, MP4 URL, file on your network) and wrap it in a themed border style. Save it as a named page like "Engine Diagnostics" or "Security Feed" and assign it to any screen.

**Keep using all your existing content.** Those MP4 loops you've already built? They work as-is. Point a video page at any file on your network or USB drive and it plays with a themed border around it. Marchog Systems doesn't replace your content library — it just makes it dramatically easier to manage and deploy.

**Stream real-time data to your screens.** This is where it gets fun. Because each screen is running a web browser, not a dumb media player, it can display live data — not just looped video. Want to see the *real* weather on Terra and not just on Hoth? A screen page can pull that in and render it in a themed display. Some ideas that are either built or easy to build:

- **Live weather** — local conditions, forecasts, severe weather alerts, rendered in a sci-fi readout
- **News headlines** — scrolling ticker or rotating cards, styled as incoming transmissions
- **Live ISS position** — real-time orbital tracking on a themed map display
- **Space launch schedule** — upcoming rocket launches with countdown timers
- **Flight tracker** — live aircraft overhead, rendered as a sensor sweep
- **Stock/crypto tickers** — financial data as a trade federation market feed
- **Home network status** — which devices are online, bandwidth usage, server health
- **Smart home data** — room temperatures, door sensors, security cameras as ship diagnostic readouts
- **Social media feeds** — YouTube sub count, Patreon milestones, latest comments as incoming comms
- **Time zones** — clocks for multiple locations styled as a galactic navigation console
- **Sports scores** — live game updates as combat status displays

The server can pull any API data on a schedule and push it to screens in real time. If it's data on the internet, it can be on your wall — themed however you want.

**Build and trigger "Scenes."** This is the big one. A Scene is a saved configuration of what every screen in your room shows at the same time. Imagine:

- **"Normal Ops"** — Each screen shows its default content, ambient loops, status displays
- **"Self-Destruct"** — Every screen flashes red warnings, countdown timers, alarms
- **"Movie Night"** — Ambient screens dim to standby, main display goes dark or shows a feed
- **"Party Mode"** — All screens cycle through animated effects and themed visuals

One button press and every screen in the room changes simultaneously.

---

## How It Actually Works

The system has three pieces:

1. **A server** running on your network (Pi, laptop, NUC, whatever). It's a lightweight Python app — no cloud, no subscriptions, no internet required after setup.

2. **Screen clients** — each display just runs a full-screen web browser pointed at the server. Can be a Pi Zero, a Fire Stick, an old Android tablet, even the browser on a smart TV. If it has a browser, it's a screen. Video loops will run beautifully on just about anything. For more complex rendered pages (3D animations, particle effects, heavy CSS), beefier hardware like a Pi 4 or an old laptop will give you smoother framerates — but even a Pi Zero handles video and data display pages without breaking a sweat.

3. **The config page** — a web-based control panel you open on your phone, tablet, or computer. This is where you manage rooms, zones, screens, pages, and scenes.

The screens talk to the server over WebSocket, so commands are instant. When you trigger a scene change or reassign a page, every screen updates within a second.

---

## What Makes This Different From Digital Signage Software

You might be thinking "there's already software for managing screens." There is — for retail stores and corporate lobbies. I've actually written digital signage solutions professionally, so I know that world well. Those tools cost money, require cloud accounts, and are designed for marketing people scheduling PowerPoint slides. I'm bringing that same technical knowledge here, but building for a completely different audience.

Marchog Systems is built for room builders. It understands that your screens are embedded in walls, hidden behind panels, and running 24/7 without a keyboard attached. It's designed for the way we use screens: always on, looping content, with the ability to dramatically change everything at once for maximum effect.

And it's free. Not freemium, not trial-period, not "free for 3 screens." Free. Open source. I built it because I needed it, and I think you might need it too.

---

## No Jedi Mind Tricks

I'm not selling anything, and I'm not going to sugarcoat where the project is. This is working software but it's still in active development. There are rough edges. Some features are built and solid, others are planned. I'm not looking for someone to tell me it's great — I'm looking for someone who will use it and tell me what's missing.

What that would look like:

- I'd get you set up with the software (happy to walk through it over a call or video chat)
- You'd grab a few pieces of hardware you probably already have — an old laptop or Pi for the server, a couple of tablets or spare screens as clients — and set it up on your workbench. No need to touch your actual room installation.
- You'd kick the tires, try assigning pages, triggering scenes, see how it feels
- You'd tell me what works, what doesn't, and what features would make this genuinely useful for your build
- Your feedback would directly shape what gets built next

The software runs on hardware you probably already have. The screens just need a browser. The server runs on anything.

---

## For Ugnaughts and Anzellans

If you want to peek under the hood, here's where things are headed.

**Local media vs. streamed video.** Right now, screens pull video over your network from the server or an external URL. That works great, but if you've got a lot of screens running high-res loops simultaneously, that's a lot of network traffic. A planned feature is remote media management — the ability to push video files directly onto client devices from the control panel and have them play locally. Best possible playback performance, minimal network load. Upload once, play forever.

**Home Assistant integration.** If you're into home automation (I am too), this is where things get really interesting. The plan is two-way integration with Home Assistant. Your scenes don't have to stop at the screens. Trigger "Self-Destruct" from Marchog Systems and it makes a call to Home Assistant to turn every light in the room red, flash the overheads, kill the music — whatever your automation can do. Or flip it around: have Home Assistant trigger the scene change in Marchog Systems while it handles the lights, sound, and fog machines on its own. One button, one voice command, one motion sensor — and the entire room transforms. Screens, lights, sound, all of it. Babu Frik would have a field day.

---

## The Short Version

**Marchog Systems replaces your USB media players with a centralized, network-based screen controller built for themed room builds.** Update any screen from your phone. Trigger coordinated "scenes" across every display with one button. Add dynamic content (not just video loops) like animated HUDs, procedural effects, and ambient displays. All free, all local, no cloud required.

If any of this sounds interesting, I'd love to show you a demo. No pressure, no commitment — just one room builder showing another room builder a tool that might make both our builds more immersive.

— John
