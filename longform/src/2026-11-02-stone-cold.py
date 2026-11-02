#!/usr/bin/env python3
"""Authoring source for the long-form video 'Stone Cold Steve Austin: full story' -> longform/2026-11-02-stone-cold.json

Markup in "say": [[caption text|spoken text]]  (captions show the first part, the voice speaks the second).
A beat without "show" continues the previous scene. "pause" = silence after the beat (s).
slot="Rxx" on a beat = real footage Ayaz saves into the Drive folder "WWE Stone Cold" (see the shot list).

Main sources (two per fact): Wikipedia "Stone Cold Steve Austin"; WWE (official YouTube titles + WWE.com);
Sports Illustrated (Apr 18 2025, Jun 21 2025); CBS Sports / TMZ (WrestleMania 41 ATV, Apr 20 2025);
Wrestling Observer (F4W), Fightful, off-road.com, Slam Wrestling, Wrestling Headlines (Oct 28 2026), 411Mania
(2026 off-road season); Wrestling Inc / PWTorch (Raw beats Nitro, Apr 13 1998); AP via Lawrence Journal-World
(Nov 26 2002); Bleacher Report / IBTimes (WCW firing).
"""
import json
import os

C = "https://upload.wikimedia.org/wikipedia/commons/"
M = {
    "austin_tx": C + "6/65/Austin_Texas_skyline_at_sunset.jpg",
    "victoria": C + "5/51/Downtown_Victoria%2C_TX_IMG_1010.JPG",
    "edna": C + "e/e4/Edna_Theatre_--_Edna%2C_TX.jpg",
    "wharton": C + "1/1c/Wharton_County_Junior_College_IMG_1049.JPG",
    "unt": C + "5/55/University_of_North_Texas_September_2015_11_%28Hurley_Administration_Building%29.jpg",
    "dallas": C + "3/31/Dallas_Skyline-01.jpg",
    "ring": C + "e/e3/Wrestling_ring.jpg",
    "atlanta": C + "b/b6/CNN_Center%2C_Atlanta%2C_Georgia.jpg",
    "yokohama": C + "1/13/Yokohama_Arena_2013.jpg",
    "ecw_arena": C + "e/ee/2300_Arena_Exterior.jpg",
    "milwaukee": C + "d/d9/Us_cellular_arena_birdseye.jpg",
    "rosemont": C + "a/a7/Allstate_Arena%2C_viewed_from_expressway_in_2023_%286283%29.jpg",
    "meadowlands": C + "d/de/Continental_arena_006.jpg",
    "msg": C + "4/4b/Madison_Square_Garden_%28MSG%29_-_Full_%2848124330357%29.jpg",
    "boston": C + "5/57/TD_Garden_2013.jpg",
    "zamboni": C + "6/68/A_Zamboni_Ice_Resurfacer.jpg",
    "corvette": C + "a/a9/Chevrolet_Corvette_C5%2C_Pau_2015_2.jpg",
    "cement": C + "f/f5/Cement_mixer_truck_-_%E8%8B%8FD0719%E6%8C%82.jpg",
    "wellsfargo": C + "5/50/Wells_Fargo_Center_-_2019_OWL_Grand_Finals.jpg",
    "astrodome": C + "5/55/Astrodome_1965.jpeg",
    "safeco": C + "0/06/Safeco_Field%2C_Seattle-.jpg",
    "hollywood_sign": C + "7/7e/The_Hollywood_sign_on_Mount_Lee_%282017-05-01%29.jpg",
    "theater": C + "5/53/Empty_Movie_Theater_Seats_%2854279616742%29.jpg",
    "mic": C + "0/02/Microphones_in_SPNN_Podcast_studio.jpg",
    "cowboys": C + "5/52/Cowboys_Stadium_full_view.jpg",
    "allegiant": C + "4/41/Allegiant_Stadium%2C_Las_Vegas%2C_Nevada_%2852259481401%29.jpg",
    "vegas_pano": C + "1/1f/Las_Vegas_Strip_panorama.jpg",
    "desert": C + "3/34/Best_in_the_Desert_2020_Vegas_to_Reno_Race_%2850236587218%29.jpg",
}

B = []


def b(say, show=None, pause=None, slot=None):
    d = {"say": say}
    if show is not None:
        d["show"] = dict(show)
        if slot:
            d["show"]["slot"] = slot
    elif slot:
        raise ValueError(f"slot {slot} on a beat without a scene: {say[:40]}")
    if pause is not None:
        d["pause"] = pause
    B.append(d)


def chapter(n, title, years, spoken=None):
    said = f"[[{title}|{spoken}]]" if spoken else title
    b(f"Chapter {['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve'][n]}. {said}.",
      {"type": "chapter", "num": n, "title": title, "kicker": years}, pause=0.6)


def photo(key, kicker=None, text=None, fit=None, **kw):
    d = {"type": "photo", "src": M[key]}
    if text:
        d["label"] = {"kicker": kicker or "", "text": text}
    if fit:
        d["fit"] = fit
    d.update(kw)
    return d


def head(kicker, text, sub=None, bg=None):
    d = {"type": "headline", "kicker": kicker, "text": text}
    if sub:
        d["sub"] = sub
    if bg:
        d["bg"] = M[bg]
    return d


def stmt(text, kicker=None, bg=None):
    d = {"type": "statement", "text": text}
    if kicker:
        d["kicker"] = kicker
    if bg:
        d["bg"] = M[bg]
    return d


def stat(kicker, value, sub, prefix="", suffix="", decimals=0, source=None, bg=None):
    d = {"type": "stat", "kicker": kicker, "value": value, "prefix": prefix, "suffix": suffix,
         "decimals": decimals, "sub": sub}
    if source:
        d["source"] = source
    if bg:
        d["bg"] = M[bg]
    return d


def vs(left, right, kicker, sub, bg=None):
    d = {"type": "versus", "left": left, "right": right, "kicker": kicker, "sub": sub}
    if bg:
        d["bg"] = M[bg]
    return d


def lst(kicker, items, title=None, bg=None):
    d = {"type": "list", "kicker": kicker, "items": items}
    if title:
        d["title"] = title
    if bg:
        d["bg"] = M[bg]
    return d


def quote(text, by, bg=None):
    d = {"type": "quote", "text": text, "by": by}
    if bg:
        d["bg"] = M[bg]
    return d


def tl(a, z, frm, to, label, kicker):
    return {"type": "timeline", "axis": [a, z], "from": frm, "to": to, "label": label, "kicker": kicker}


WWF, WCW, WWE = "[[WWF|W W F]]", "[[WCW|W C W]]", "[[WWE|W W E]]"

# ------------------------------------------------------------------ COLD OPEN
b(f"In September [[1995|nineteen ninety-five]], {WCW} fired an injured wrestler over the phone, "
  "because the man running the company did not see him as marketable.",
  head("Sept 15, 1995 · WCW", "Fired. *Not marketable.*"), slot="R29")
b("He was thirty years old. He had a torn triceps, no job, and his old employer had decided "
  "he would never be a star.",
  stmt("Age 30. No job. *Never a star.*"), slot="R03")
b(f"Two and a half years later, he was the champion of the {WWF}.",
  tl(1995, 1999, 1995.7, 1998.24, "WWF Champion", "Two and a half years"), slot="R11")
b("He drank beer in the ring, he attacked his own boss on live television, "
  f"and he helped the {WWF} win the Monday Night War.",
  lst("Stone Cold", ["Beer in the ring", "Stunned his own boss", "Won the Monday Night War"]), slot="R05")
b(f"By [[2001|two thousand one]], the {WWF} owned {WCW}, the company that had let him go.",
  head("March 2001", "The WWF buys the company that *fired him*"))
b("But the highlight reels skip the hard parts.",
  stmt("The highlight reels skip the *hard parts*."))
b("A piledriver that left him temporarily paralyzed. A walkout that nearly ended his career. "
  "A last match at thirty-eight. And a comeback, nineteen years later.",
  lst("The parts people skip", ["A piledriver. Temporary paralysis.", "The walkout", "A last match at 38",
                                "A comeback 19 years later"]))
b("This is the full story of Stone Cold Steve Austin. Where he came from, how he got famous, everything he won, "
  "why he walked away, and what he is doing right now, at the end of [[2026|twenty twenty-six]]. "
  "And yes, it involves a race car with the number [[316|three sixteen]] on it.",
  {"type": "title", "kicker": "The full story", "text": "Stone *Cold*", "sub": "1964 — 2026"}, pause=0.8,
  slot="R58")

# ------------------------------------------------------------------ 1
chapter(1, "Texas tough", "1964 — 1989")
b("He was born Steven James Anderson, on [[December 18, 1964|December eighteenth, nineteen sixty-four]], "
  "in Austin, Texas.",
  photo("austin_tx", "Austin, Texas", "Born *Dec 18, 1964*", fit="frame"))
b("Yes, Austin. But that name came much later, and almost by accident.",
  stmt("The name came *later*."))
b("His parents divorced when he was young, and his mother raised him and his brothers in Victoria, "
  "in South Texas.",
  photo("victoria", "Victoria, Texas", "Raised by his *mother*"))
b("She married a man named Ken Williams, who adopted the children. Steven Anderson became Steven Williams, "
  "and the family settled in Edna, a small town about a hundred miles southwest of Houston.",
  head("A new name", "Steve *Williams*", "the family settles in Edna, Texas", bg="edna"))
b("Almost everything in the first half of his life happened inside one state.",
  {"type": "map", "kicker": "A Texas life",
   "view": [-101.5, -93.5, 26.8, 34.6],
   "points": [["Austin", 30.27, -97.74], ["Victoria", 28.81, -96.99], ["Edna", 28.98, -96.65],
              ["Wharton", 29.31, -96.10], ["Denton", 33.21, -97.13], ["Dallas", 32.78, -96.80]]})
b("At Edna High School, he played football all four years, as a running back.",
  photo("edna", "Edna, Texas", "Four years of *football*"))
b("Football took him to Wharton County Junior College, where he played linebacker for one year. "
  "A strong season there earned him a full scholarship to the University of North Texas.",
  photo("wharton", "Wharton County Junior College", "Then a full *scholarship*"))
b("At North Texas, he played linebacker, and then defensive end after a knee injury.",
  photo("unt", "University of North Texas · Denton", "Linebacker, then *defensive end*"))
b("But he left college a few credits short of a degree.",
  stmt("A few credits *short*."))
b("He ended up in Dallas, loading and unloading trucks on a freight dock.",
  photo("dallas", "Dallas", "Loading *trucks*"))
b("And Dallas, it turned out, was one of the best places in America to learn how to wrestle.", pause=0.8)

# ------------------------------------------------------------------ 2
chapter(2, "Stunning", "1989 — 1995")
b("The city's wrestling home was the Sportatorium, an old arena where World Class Championship Wrestling "
  "had made the Von Erich family famous.",
  photo("ring", "The Dallas Sportatorium", "Home of *World Class* wrestling"))
b("One of that promotion's stars, the British wrestler Chris Adams, ran a wrestling school there. "
  "Steve signed up.",
  head("Dallas", "Trained by *Chris Adams*", "at the Sportatorium", bg="dallas"))
b("He wrestled his first matches as Steve Williams. But wrestling already had a famous Steve Williams, "
  "Doctor Death. So the promoters gave him a new last name. Austin.",
  head("The new name", "Steve *Austin*", "there was already a 'Dr. Death' Steve Williams"))
b("In [[1991|nineteen ninety-one]], World Championship Wrestling, Ted Turner's company in Atlanta, signed him.",
  photo("atlanta", "WCW · Atlanta", "Signed by *WCW*"))
b("They called him Stunning Steve Austin. Long bleached hair, a cocky villain, and very good in the ring.",
  head("WCW · 1991", "*Stunning* Steve Austin"), slot="R03")
b(f"In June [[1991|ninety-one]], he won the {WCW} Television Championship. He would hold it twice.",
  stat("WCW · 1991 — 1992", 2, "Television Championship reigns", suffix="×"), slot="R03")
b("In [[1993|ninety-three]], the company paired him with Brian Pillman. As the Hollywood Blonds, "
  "they won the world tag team titles, and fans loved them.",
  head("1993", "The Hollywood *Blonds*", "with Brian Pillman · world tag team champions"), slot="R03")
b(f"{WCW} split them up anyway.",
  stmt("WCW split them *up* anyway."))
b("At Starrcade, in December [[1993|ninety-three]], Austin beat Dustin Rhodes for the United States title, "
  "and he held it for eight months, until Ricky Steamboat took it from him.",
  vs("Steve Austin", "Dustin Rhodes", "Starrcade 1993", "Austin wins the United States title"), slot="R03")
b("Then came the night that summed up his time there. At Fall Brawl [[1994|ninety-four]], he was handed the "
  "title back by forfeit, and he lost it to Hacksaw Jim Duggan in thirty-five seconds.",
  stat("Fall Brawl 1994", 35, "seconds — and the title was gone", suffix=" sec"))
b(f"Hulk Hogan had just arrived in {WCW}, and the company was building around big names from the "
  "[[1980s|nineteen eighties]]. Austin was being pushed down the card.",
  stmt("Pushed *down* the card."))
b("In [[1995|ninety-five]], on a tour of Japan, he tore his triceps.",
  photo("yokohama", "Japan · 1995", "A torn *triceps*"))
b(f"And on [[September 15, 1995|September fifteenth, nineteen ninety-five]], while he was at home recovering, "
  f"Eric Bischoff, the president of {WCW}, fired him.",
  head("Sept 15, 1995", "Fired by *Eric Bischoff*", "while he was injured"), slot="R29")
b("Bischoff has explained it simply. He did not see Austin as marketable.",
  stmt("Not *marketable*."), pause=0.8)

# ------------------------------------------------------------------ 3
chapter(3, "Superstar", "1995")
b("One man disagreed. Paul Heyman ran Extreme Championship Wrestling, a small and wild promotion that "
  "filled a former bingo hall in Philadelphia.",
  photo("ecw_arena", "ECW Arena · Philadelphia", "Paul Heyman's *ECW*"))
b("Austin's arm was not ready for full matches. So Heyman paid him around five hundred dollars a night, "
  "mostly just to talk.",
  stat("ECW · 1995", 500, "a night — mostly to talk", prefix="$"), slot="R08")
b(f"For the first time, nobody told him what to say. He called {WCW}'s [[TV|T V]] show Monday NyQuil. "
  "He did a mocking impression of Hulk Hogan. And he went after Eric Bischoff by name.",
  lst("The ECW promos", ["'Monday NyQuil'", "A Hulk Hogan impression", "Eric Bischoff, by name"]), slot="R08")
b("He called himself Superstar Steve Austin. And people in the business started to notice. "
  "This guy could really talk.",
  head("ECW · 1995", "*Superstar* Steve Austin", "the promos that changed his career"), slot="R08")
b(f"Jim Ross, who worked in the {WWF} office, and the wrestler Diesel helped convince Vince McMahon "
  "to sign him.",
  head("Late 1995", "The WWF *calls*", "Jim Ross and Diesel vouched for him"))
b("Three months after being fired, Steve Austin was on his way to the biggest wrestling company in the world.",
  tl(1995, 1996.5, 1995.7, 1995.96, "Signed by the WWF", "Three months"), pause=0.8)

# ------------------------------------------------------------------ 4
chapter(4, "Austin 3:16", "1996", spoken="Austin three sixteen")
b(f"The {WWF}'s first idea was not great. On Raw in January [[1996|nineteen ninety-six]], he debuted as "
  "The Ringmaster, a quiet technical wrestler managed by Ted DiBiase.",
  head("Raw · Jan 8, 1996", "*The Ringmaster*", "managed by Ted DiBiase"), slot="R09")
b("DiBiase handed him the Million Dollar Championship. His opponent that night was a young Matt Hardy.",
  head("His WWF debut", "The *Million Dollar* Champion", "his opponent: a young Matt Hardy"), slot="R09")
b("Austin did not like the name. He wanted something with an edge, and he did not like the ideas the office sent him.",
  stmt("He needed a *name*."))
b("The answer came from home. His wife at the time, Jeanie, made him a cup of tea, and told him "
  "to drink it before it got stone cold.",
  stmt("Drink your tea before it gets *stone cold*."))
b("He shaved his head, grew a goatee, and wore plain black trunks. By March, he was Stone Cold Steve Austin.",
  head("March 1996", "*Stone Cold* Steve Austin", "his first match under the new name"), slot="R09")
b("He was a villain who did not care about anybody. And on [[June 23, 1996|June twenty-third, nineteen "
  "ninety-six]], he won the King of the Ring tournament, in Milwaukee.",
  photo("milwaukee", "King of the Ring · Milwaukee", "*June 23, 1996*"), slot="R01")
b("In the final, he beat Jake The Snake Roberts, whose character had found religion and quoted the Bible.",
  vs("Steve Austin", "Jake Roberts", "King of the Ring 1996 · final", "Austin wins with the Stunner"), slot="R01")
b("Then Austin grabbed the microphone, and mocked him. Talk about your psalms, he said. "
  "Talk about John [[3:16|three sixteen]].",
  stmt("Then he grabbed the *microphone*."), slot="R01")
b("Austin [[3:16|three sixteen]] says I just whipped your ass.",
  quote("Austin 3:16 says I just whipped your ass.", "King of the Ring, June 23, 1996"), slot="R01")
b(f"Fans started bringing signs. The {WWF} printed a black T-shirt with Austin [[3:16|three sixteen]] on the "
  "back, and it became one of the best-selling shirts in wrestling history.",
  head("The shirt", "*Austin 3:16*", "one of the best-selling shirts in wrestling history"))
b(f"Today, {WWE} marks March sixteenth every year as Austin [[3:16|three sixteen]] Day.",
  head("Every year", "March 16 is *3:16 Day*"), slot="R30")
b("But in [[1996|ninety-six]], he was still a bad guy. To become the biggest star in the world, "
  "he needed the right opponent.", pause=0.8)

# ------------------------------------------------------------------ 5
chapter(5, "The double turn", "1997")
b("He found him in Bret Hart, Canada's biggest wrestling star, and the opposite of Austin in every way. "
  "Polished, proud, and a hero.",
  head("The rival", "Bret *Hart*", "the Excellence of Execution"), slot="R02")
b("At Survivor Series, Hart beat him after almost half an hour. "
  "In January [[1997|nineteen ninety-seven]], Austin won the Royal Rumble.",
  lst("The build", ["Survivor Series 1996: Hart wins", "Royal Rumble 1997: Austin wins"]))
b("Then came WrestleMania [[13|thirteen]], on [[March 23, 1997|March twenty-third, nineteen ninety-seven]], "
  "just outside Chicago. A submission match. No disqualifications. "
  "And the [[UFC|U F C]] fighter Ken Shamrock as the special referee.",
  photo("rosemont", "WrestleMania 13 · Rosemont, Illinois", "A *submission* match"), slot="R02")
b("By the end, Austin was bleeding, and he was trapped in Hart's Sharpshooter.",
  vs("Stone Cold", "Bret Hart", "WrestleMania 13", "No-DQ submission match · Ken Shamrock referees"), slot="R02")
b("He would not quit. He screamed, he fought it, and then he passed out. Shamrock stopped the match.",
  stmt("He never *quit*. He passed out."), slot="R02")
b("Hart won. But Hart kept attacking a beaten man after the bell, and the crowd turned. "
  "The hero became the villain. The villain who refused to give up became the hero.",
  head("WrestleMania 13", "The *double turn*", "Hart became the villain. Austin became the hero."), slot="R02")
b(f"In [[2025|twenty twenty-five]], {WWE} made that match the first Immortal Moment in its Hall of Fame.",
  head("WWE Hall of Fame · 2025", "The first *Immortal Moment*"), slot="R26")
b("Five months later came the night that changed the rest of his career.",
  stmt("Then came *SummerSlam*."))
b("On [[August 3, 1997|August third, nineteen ninety-seven]], Owen Hart, Bret's brother, gave him a "
  "piledriver, and it went wrong. Austin landed on the top of his head.",
  photo("meadowlands", "SummerSlam · East Rutherford, NJ", "*Aug 3, 1997*"), slot="R10")
b("He suffered a bruised spinal cord, and for a short time, he could not move.",
  head("The injury", "A bruised *spinal cord*", "temporary paralysis"), slot="R10")
b("He still managed to roll Owen up for the pin, and he won the Intercontinental Championship.",
  vs("Stone Cold", "Owen Hart", "SummerSlam 1997", "Austin wins the Intercontinental title"), slot="R10")
b("He was forced to give up his titles. But he did not stay away for long.",
  stmt("He did not stay away for *long*."))
b(f"On [[September 22, 1997|September twenty-second, nineteen ninety-seven]], Raw went to Madison Square "
  "Garden for the first time. And Austin gave a Stone Cold Stunner to the owner of the company, Vince McMahon.",
  photo("msg", "Raw · Madison Square Garden", "A *Stunner* for the boss"), slot="R04")
b("Police led him out in handcuffs, as part of the show. Fans had never seen anything like it. "
  "An employee, attacking his boss.",
  head("Sept 22, 1997", "Arrested for *the Stunner*", "all part of the show"), slot="R04")
b(f"That one moment became the story the {WWF} would ride for the next two years.", pause=0.8)

# ------------------------------------------------------------------ 6
chapter(6, "Austin versus McMahon", "1998")
b("In January [[1998|ninety-eight]], Austin won his second Royal Rumble, eliminating The Rock last.",
  head("Royal Rumble 1998", "Rumble win *No. 2*", "last man out: The Rock"))
b("Then WrestleMania [[XIV|fourteen]], in Boston, on [[March 29, 1998|March twenty-ninth, nineteen ninety-eight]]. "
  f"Austin against Shawn Michaels, for the {WWF} Championship.",
  photo("boston", "WrestleMania XIV · Boston", "Austin vs. *Shawn Michaels*"), slot="R11")
b("The special enforcer was the boxer Mike Tyson. When Austin hit the Stunner, Tyson slid in, "
  "counted the three himself, and then knocked Michaels out.",
  vs("Stone Cold", "Shawn Michaels", "WrestleMania XIV", "Mike Tyson counts the pin"), slot="R11")
b(f"Two and a half years after {WCW} fired him, Steve Austin was the {WWF} Champion.",
  tl(1995, 1999, 1995.7, 1998.24, "WWF Champion", "From fired to champion"), slot="R11")
b("Now Vince McMahon played the evil boss on [[TV|T V]], and Austin played every worker who ever wanted to "
  "punch his manager.",
  head("1998", "The worker vs. *the boss*"), slot="R14")
b(f"On [[April 13, 1998|April thirteenth, nineteen ninety-eight]], Raw promised Austin against McMahon in a match. "
  f"It never really happened, but that night Raw beat {WCW}'s Nitro in the ratings for the first time "
  "in eighty-three weeks.",
  stat("Raw · April 13, 1998", 83, "weeks — Nitro's winning streak, broken"), slot="R14")
b("Then it got ridiculous, in the best way. Austin drove a Zamboni to the ring and jumped McMahon.",
  photo("zamboni", "1998", "A *Zamboni*"), slot="R12")
b("He filled McMahon's Corvette with cement.",
  photo("cement", "1998", "Cement in the *Corvette*"), slot="R13")
b("And in [[1999|ninety-nine]], he drove a beer truck to the ring, and hosed down McMahon, his son Shane "
  "and The Rock with beer.",
  head("1999", "The *beer truck*", "McMahon, Shane and The Rock, soaked"), slot="R05")
b("Every night ended the same way. The glass shattered, Austin walked in, and two cans of beer met "
  "in the middle of the ring.",
  stmt("Glass shatters. *Two beers.*", bg="ring"), slot="R58")
b(f"With Austin on top, the {WWF} took over the Monday Night War. In March [[2001|two thousand one]], "
  f"it bought {WCW} outright.",
  head("March 2001", "The WWF buys *WCW*"))
b("But all those Stunners came at a price. The neck that Owen Hart's piledriver had hurt was getting worse.",
  pause=0.8)

# ------------------------------------------------------------------ 7
chapter(7, "Broken", "1999 — 2000")
b("At WrestleMania [[XV|fifteen]], in Philadelphia, he beat The Rock and took the title back.",
  photo("wellsfargo", "WrestleMania XV · Philadelphia", "Austin beats *The Rock*"), slot="R31")
b("He was the face of the company. He was also in constant pain.",
  stmt("The face of the company. In *constant pain*."))
b("By late [[1999|ninety-nine]], his neck was bad enough that there was a real threat he would have to retire "
  "early. Doctors advised surgery.",
  head("Late 1999", "A real threat of *retirement*", "doctors advised neck surgery"))
b(f"So, on [[November 14, 1999|November fourteenth, nineteen ninety-nine]], at Survivor Series, the {WWF} "
  "wrote him off television. He was run over by a car in the parking lot. On the show, of course.",
  head("Survivor Series 1999", "Run over by a *car*", "a storyline to write him off TV"))
b("Austin later called it the worst storyline he was ever part of.",
  stmt("'The worst storyline' he was ever part of."))
b("He had the surgery, and he was gone for most of the next year.",
  stmt("Surgery. *Gone for most of a year.*"))
b("He came back at Unforgiven, in September [[2000|two thousand]], to find out who had run him down. "
  "It was Rikishi.",
  head("Unforgiven · Sept 24, 2000", "*Rikishi* did it"), slot="R15")
b("Then the story made Triple H the man behind it all. At Survivor Series, Austin lifted Triple H's car "
  "with a forklift, and dropped it twenty feet.",
  stat("Survivor Series 2000", 20, "feet — Triple H's car, dropped from a forklift", suffix=" ft"))
b("He was back, and he was still the biggest star in the company. Then he did the one thing nobody expected.",
  pause=0.8)

# ------------------------------------------------------------------ 8
chapter(8, "Selling out", "2001 — 2002")
b("In January [[2001|two thousand one]], he won his third Royal Rumble. Nobody has won more.",
  stat("Royal Rumble · 2001", 3, "wins — still the record", suffix="×"))
b("At WrestleMania [[X-Seven|ex seven]], on [[April 1, 2001|April first, two thousand one]], "
  "in the Houston Astrodome, he faced The Rock again, in his home state.",
  photo("astrodome", "WrestleMania X-Seven · Houston", "Austin vs. *The Rock*"), slot="R16")
b("To win, he did the unthinkable. He let Vince McMahon help him beat The Rock. Then he shook McMahon's hand.",
  head("April 1, 2001", "He shook *McMahon's* hand"), slot="R16")
b("Stone Cold had sold out. He was a villain for the first time since [[1997|nineteen ninety-seven]], "
  "and that night was the first WrestleMania to pass a million buys.",
  lst("WrestleMania X-Seven", ["Austin wins his 5th WWF title", "He turns heel", "First WrestleMania over 1 million buys"]),
  slot="R16")
b("He teamed with Triple H, as the Two-Man Power Trip, and they won the tag team titles.",
  head("2001", "The Two-Man *Power Trip*", "with Triple H · tag team champions"))
b("And he got funny. Heel Austin was needy and paranoid. He bought gifts for McMahon and Kurt Angle, "
  "and he started answering everything with one word. What? Until whole arenas said it with him.",
  lst("Heel Austin, 2001", ["Gifts for Mr. McMahon", "Gifts for Kurt Angle", "What? What? What?"]), slot="R17")
b(f"That summer, {WCW} and [[ECW|E C W]] invaded. Austin turned on the {WWF} and joined the invaders.",
  head("July 2001 · Invasion", "Austin joins *the Alliance*"))
b("He lost the title to Kurt Angle in September, won it back in October, his sixth reign, "
  "and lost it to Chris Jericho in December.",
  lst("Fall 2001", ["Sept: loses the title to Kurt Angle", "Oct: wins it back — reign No. 6",
                    "Dec: loses to Chris Jericho"]))
b("Then [[2002|two thousand two]] went wrong.",
  stmt("Then *2002* went wrong."))
b("He was booked to lose to the young Brock Lesnar, on a regular episode of Raw, with no build-up. "
  "On [[June 10, 2002|June tenth, two thousand two]], he did not show up. He went home to Texas.",
  head("June 10, 2002", "The *walkout*", "he would not lose to Lesnar with no build-up"))
b("He has said since that he regrets how he handled it.",
  stmt("He *regrets* how he handled it."))
b("That summer, there was trouble at home as well. Police were called after a domestic dispute with his "
  "then-wife, Debra. In November, he pleaded no contest to a misdemeanor charge, and he was given probation.",
  head("2002", "Trouble *at home*", "a no-contest plea and probation"))
b("For eight months, Stone Cold was gone.", stmt("For eight months, he was *gone*."), pause=0.8)

# ------------------------------------------------------------------ 9
chapter(9, "The last match", "2003 — 2004")
b("He came back in February [[2003|two thousand three]], at No Way Out. And his first opponent was the new "
  "boss of Raw. Eric Bischoff. The man who had fired him.",
  vs("Stone Cold", "Eric Bischoff", "No Way Out · Feb 23, 2003", "The man who fired him"))
b("Austin won. Of course he did.", stmt("Of course he *won*."))
b("But his body was done. His neck, and years of damage to his knees.",
  stmt("His body was *done*."))
b("WrestleMania [[XIX|nineteen]], in Seattle, on [[March 30, 2003|March thirtieth, two thousand three]]. "
  "The third and last WrestleMania match between Austin and The Rock.",
  photo("safeco", "WrestleMania XIX · Seattle", "Austin vs. Rock, *part three*"), slot="R19")
b("The Rock hit him with three Rock Bottoms, and won. The rivalry that had defined an era was over.",
  vs("The Rock", "Stone Cold", "WrestleMania XIX", "Rock wins · the last match of the trilogy"), slot="R19")
b("It was Austin's last match. He was thirty-eight years old.",
  stmt("His last match. *Age 38.*"), slot="R19")
b("But he did not disappear. In April, he became the co-general manager of Raw, and later, its Sheriff. "
  "Mostly, that meant drinking beer and stunning anyone who annoyed him.",
  head("2003 — 2004", "Sheriff of *Raw*"), slot="R20")
b("At WrestleMania [[XX|twenty]], back at Madison Square Garden, he was the special referee for "
  "Brock Lesnar against Goldberg. He stunned them both.",
  photo("msg", "WrestleMania XX · Madison Square Garden", "Special referee: *Stone Cold*"))
b("Then he left wrestling for Hollywood. Mostly.", pause=0.8)

# ------------------------------------------------------------------ 10
chapter(10, "Life after the ring", "2005 — 2021")
b("His first big movie role came in [[2005|two thousand five]], as a prison guard in The Longest Yard, "
  "with Adam Sandler and Chris Rock.",
  photo("theater", "2005", "*The Longest Yard*"), slot="R22")
b("In [[2007|two thousand seven]], The Condemned gave him his first starring role. And in [[2010|twenty ten]], "
  "he joined Sylvester Stallone in The Expendables.",
  lst("Hollywood", ["The Longest Yard — 2005", "The Condemned — 2007", "The Expendables — 2010"], bg="theater"),
  slot="R22")
b("In December [[2007|two thousand seven]], he also made it official. Steve Austin became his legal name.",
  head("December 2007", "*Steve Austin*, legally"))
b(f"In [[2009|two thousand nine]], he went into the {WWE} Hall of Fame. He was inducted by Vince McMahon, "
  "the man he had stunned more times than anyone can count.",
  head("2009", "WWE *Hall of Fame*", "inducted by Vince McMahon"), slot="R21")
b("Then he found a new way to talk to fans. In [[2013|twenty thirteen]], he started The Steve Austin Show, "
  "a podcast where he interviewed wrestlers and talked about anything he liked.",
  photo("mic", "2013", "The Steve Austin *Show*"))
b("On [[TV|T V]], he hosted Broken Skull Challenge on [[CMT|C M T]], an obstacle course show where the winner "
  "took home ten thousand dollars.",
  stat("Broken Skull Challenge · CMT", 10000, "for the winner", prefix="$"), slot="R23")
b(f"Then came Straight Up Steve Austin on the [[USA|U S A]] Network, and The Broken Skull Sessions for {WWE}, "
  "long interviews with the stars he once worked with.",
  lst("On screen", ["Broken Skull Challenge — CMT, 2014", "Straight Up Steve Austin — USA, 2019",
                    "The Broken Skull Sessions — 2019"]), slot="R23")
b("He put his name on a beer, Broken Skull, with El Segundo Brewing, and he spent his free time "
  "at his Broken Skull Ranch in South Texas.",
  head("The business", "*Broken Skull*", "a beer, a ranch, a brand"))
b("For nineteen years, it looked like he was done with the ring for good.",
  stmt("For *19 years*, he was done."), pause=0.8)

# ------------------------------------------------------------------ 11
chapter(11, "One more beer", "2022 — 2025")
b("In March [[2022|twenty twenty-two]], Kevin Owens spent weeks insulting Texas on [[TV|T V]], and invited Austin "
  "onto his talk show, at WrestleMania [[38|thirty-eight]], in Arlington, Texas.",
  photo("cowboys", "WrestleMania 38 · Arlington, Texas", "An invitation from *Kevin Owens*"), slot="R24")
b("On [[April 2, 2022|April second, twenty twenty-two]], Austin came out, and the talk show turned into a "
  "No Holds Barred match.",
  head("April 2, 2022", "The talk show becomes a *match*", "No Holds Barred"), slot="R24")
b("At fifty-seven, after nineteen years away, he beat Owens with a Stunner, and drank beer with the crowd.",
  stat("WrestleMania 38", 19, "years since his last match", suffix=" yrs"), slot="R24")
b("The next night, he came back out, and gave a Stunner to Vince McMahon. One more time.",
  head("April 3, 2022", "One more Stunner for *Vince*"), slot="R25")
b("In April [[2025|twenty twenty-five]], in Las Vegas, he and Bret Hart went into the Hall of Fame together, "
  "for WrestleMania [[13|thirteen]].",
  vs("Stone Cold", "Bret Hart", "WWE Hall of Fame · April 2025", "Together again · the first Immortal Moment"),
  slot="R26")
b("That weekend, he said he was not looking to get back in the ring, because the young wrestlers "
  "needed something to shoot for.",
  stmt("Not looking to get back in the *ring*."), slot="R26")
b("Two nights later, at WrestleMania [[41|forty-one]], he rode an [[ATV|A T V]] out to announce the "
  "attendance. It did not go as planned.",
  photo("allegiant", "WrestleMania 41 · Las Vegas", "The *ATV* entrance"), slot="R27")
b("He crashed into the barricade at ringside, and a fan in the front row was knocked over. "
  "He said afterwards that he was embarrassed.",
  head("April 20, 2025", "The *ATV* crash", "he said he was embarrassed"), slot="R27")
b("So, what does a retired wrestler do in his sixties? He goes racing.", pause=0.8)

# ------------------------------------------------------------------ 12
chapter(12, "Where is he now?", "2026")
b("In [[2026|twenty twenty-six]], Austin ran his first full season of competitive off-road racing, in the Nevada desert.",
  photo("desert", "Nevada · 2026", "A rookie *racer* at 61"), slot="R28")
b("He drives a Kawasaki in the Stock Mod class of the Valley Off-Road Racing Association, for his own team, "
  "Broken Skull Racing. The car's number is [[316|three sixteen]].",
  head("Broken Skull Racing", "Car *No. 316*", "VORRA · Stock Mod class"), slot="R28")
b("He won his class in each of his first two races.",
  stmt("Class wins in his first *two races*."), slot="R28")
b("Not every race went that well. In August, a mistake at the Stomping Grounds [[300|three hundred]] ended "
  "his race early and damaged the car. And at the season finale in October, he could not finish the second race.",
  lst("Season one", ["Class wins in his first two races", "Out early at the Stomping Grounds 300",
                      "Did not finish at the Monster Dash"]))
b("But he is already planning [[2027|twenty twenty-seven]]. Same class. More races.",
  head("2027", "Same class. *More races.*"), slot="R28")
b(f"{WWE} still calls on him, too. He was booked for its fan event during WrestleMania [[42|forty-two]] "
  "weekend in Las Vegas this April, and every few months a new rumor says he might wrestle one more time.",
  head("2026", "One more *match*?", "a rumor, not a booking", bg="vegas_pano"))
b("He has said he could still do it. He just does not know if he wants to.",
  stmt("He could. Does he *want to*?"))
b(f"Here is what he left in the ring. Six {WWF} Championships. Two Intercontinental titles. "
  "Three Royal Rumble wins, still the record. The [[1996|nineteen ninety-six]] King of the Ring. "
  f"The company's fifth Triple Crown champion. And in {WCW}, two Television titles, two United States titles "
  "and a world tag team title.",
  lst("Career", ["6× WWF Champion", "2× Intercontinental Champion", "3× Royal Rumble winner — the record",
                 "1996 King of the Ring", "WCW: 2× TV · 2× US · 1× tag"]), slot="R59")
b("But the titles are not why people still wear the shirt.",
  stmt("The titles aren't the *point*."))
b("He got fired, he got hurt, and he got told he was not marketable. And he turned all of it into "
  "the biggest star of the Attitude Era.",
  head("The legacy", "Fired. Hurt. *Unstoppable.*"), slot="R59")
b(f"And it started with a phone call from {WCW}, and a cup of tea.",
  head("Where it started", "A phone call and a cup of *tea*"), slot="R59", pause=0.6)
b("Triple H's story is next on this channel. Subscribe, so you do not miss it.",
  {"type": "end", "kicker": "Next on the channel", "text": "Triple H: the *full story*",
   "cta": "Subscribe", "follow": "New WWE stories every week"})
b("And tell me in the comments. What is the greatest Stone Cold moment of all time? "
  "WrestleMania [[13|thirteen]], the beer truck, or the first Stunner on Vince?",
  {"type": "end", "kicker": "Your take", "text": "The greatest Stone Cold moment *ever?*",
   "cta": "Tell us below ↓", "follow": "Subscribe for the next story"})

# ------------------------------------------------------------------ on-screen credit per slot
SLOT_CREDIT = {s: "WWE" for s in ("R01", "R02", "R04", "R05", "R08", "R09", "R10", "R11", "R12", "R13", "R14",
                                   "R15", "R16", "R17", "R19", "R20", "R21", "R24", "R25", "R26", "R27", "R29",
                                   "R30", "R31", "R58", "R59")}
SLOT_CREDIT.update({"R03": "WCW / WWE", "R22": "Paramount / Lionsgate", "R23": "CMT / USA Network / WWE",
                    "R28": "Broken Skull Racing", "R60": ""})
used = {x["show"]["slot"] for x in B if "show" in x and "slot" in x["show"]}
assert used <= set(SLOT_CREDIT), used - set(SLOT_CREDIT)

job = {
    "id": "2026-11-02-stone-cold",
    "format": "longform",
    "title": "How Stone Cold Went From Fired to WWE Icon | Full Story",
    "voice": {"tts": "kokoro", "voice": "am_michael", "speed": 1.03},
    "music": {"gen": "ambient", "gain_db": -24},
    "thumbnail": {"kicker": "Stone Cold Steve Austin", "text": "Fired to *icon*", "sub": "The full story",
                  "slot": "R60", "sharp": True, "focus": [0.5, 0.22], "big": "3:16"},
    "slot_credit": SLOT_CREDIT,
    "slot_in": {},
    "beats": B,
}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-02-stone-cold.json")
json.dump(job, open(out, "w"), ensure_ascii=False, indent=1)


def spoken(s):
    import re
    return re.sub(r"\[\[[^|\]]*\|([^\]]*)\]\]", r"\1", s)


words = sum(len(spoken(x["say"]).split()) for x in B)
print(f"{len(B)} beats, ~{words} spoken words (~{words / 150:.1f} min), scenes: {sum(1 for x in B if 'show' in x)}, "
      f"footage slots: {len(used)}")
