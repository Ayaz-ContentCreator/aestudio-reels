#!/usr/bin/env python3
"""Authoring source for the long-form video 'The Rock: full story' -> longform/2026-11-02-the-rock.json

Markup in "say": [[caption text|spoken text]]  (captions show the first part, the voice speaks the second).
A beat without "show" continues the previous scene. "pause" = silence after the beat (s).
"""
import json
import os

C = "https://upload.wikimedia.org/wikipedia/commons/"
M = {
    "hayward": C + "4/4a/Green_Shutter_Hotel%2C_Hayward%2C_California_-_Stierch.jpg",
    "ring": C + "e/e3/Wrestling_ring.jpg",
    "hamden": C + "8/89/Hamden_High_School.jpg",
    "auckland": C + "b/b5/AucklandPano_MC.jpg",
    "waikiki": C + "0/03/View_of_Waikiki_from_Diamond_Head.jpg",
    "bethlehem": C + "e/eb/Greetings_from_Bethlehem%2C_Pennsylvania_-_Large_Letter_Postcard_%284237042655%29.jpg",
    "umiami": C + "0/0f/Coral_Gables_-_University_of_Miami_campus.jpg",
    "orangebowl": C + "6/69/Miami_orange_bowl_stadium_cropped.jpg",
    "mcmahon": C + "9/95/McMahon_Stadium_with_Calgary_skyline_in_background.jpg",
    "calgary": C + "7/72/Calgary_Skyline_from_the_river.jpg",
    "memphis": C + "0/03/Skyline_of_Memphis%2C_TN.jpg",
    "msg": C + "4/4b/Madison_Square_Garden_%28MSG%29_-_Full_%2848124330357%29.jpg",
    "nyc_video": C + "0/0d/Aerial_views_of_Chrysler_Building%2C_42nd_Street%2C_One_Vanderbilt%2C_Empire_State_Building%2C_Grand_Central_Station_and_New_York_City%2C_USA_skyline.webm",
    "wellsfargo": C + "5/50/Wells_Fargo_Center_-_2019_OWL_Grand_Finals.jpg",
    "universal": C + "8/8e/Universal_Studios_Hollywood_globe_%28July_2022%29.JPG",
    "astrodome": C + "5/55/Astrodome_1965.jpeg",
    "cntower": C + "2/2d/Toronto_-_ON_-_CN_Tower_bei_Nacht2.jpg",
    "toronto_video": C + "9/94/Toronto_Skyline.webm",
    "safeco": C + "0/06/Safeco_Field%2C_Seattle-.jpg",
    "hollywood_sign": C + "7/7e/The_Hollywood_sign_on_Mount_Lee_%282017-05-01%29.jpg",
    "hollywood_video": C + "6/64/Aerial_views_of_Hollywood_Sign%2C_Hollywoodland%2C_Griffith_Observatory%2C_Los_Feliz_and_Hollywood_Heights%2C_Los_Angeles%2C_California%2C_USA.webm",
    "theater": C + "5/53/Empty_Movie_Theater_Seats_%2854279616742%29.jpg",
    "projector": C + "8/89/Film_projector_%28Cinema-vikonda%2C_Koryazhma%29.jpg",
    "georgiadome": C + "3/3e/2013.01.26.110220_Georgia_Dome_Atlanta_Georgia.jpg",
    "hardrock": C + "a/a4/200127-H-PX819-0092_-_49451830343.jpg",
    "metlife": C + "b/b4/MetLife_Stadium_exterior_Super_Bowl_XLVIII.jpg",
    "cowboys": C + "5/52/Cowboys_Stadium_full_view.jpg",
    "star": C + "4/45/Dwayne_Johnson_star_%28Hollywood_Walk_of_Fame_stars%29.jpg",
    "nyse": C + "7/71/Sign_of_the_New_York_Stock_Exchange%2C_Broad_Street.jpg",
    "linc": C + "7/70/Lincoln_Financial_Field.jpg",
    "superdome": C + "7/75/Caesars_Superdome_New_Orleans%2C_LA.jpg",
    "vegas_video": C + "5/55/Flight_over_the_Las_Vegas_strip_in_the_early_morning.webm",
    "vegas_pano": C + "1/1f/Las_Vegas_Strip_panorama.jpg",
    "venice": C + "d/df/Palazzo_del_cinema.png",
}

B = []


def b(say, show=None, pause=None):
    d = {"say": say}
    if show is not None:
        d["show"] = show
    if pause is not None:
        d["pause"] = pause
    B.append(d)


def chapter(n, title, years):
    b(f"Chapter {['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve'][n]}. {title}.",
      {"type": "chapter", "num": n, "title": title, "kicker": years}, pause=0.6)


def photo(key, kicker=None, text=None, fit=None, **kw):
    d = {"type": "photo", "src": M[key]}
    if text:
        d["label"] = {"kicker": kicker or "", "text": text}
    if fit:
        d["fit"] = fit
    d.update(kw)
    return d


def video(key, at, kicker=None, text=None, **kw):
    d = {"type": "video", "src": M[key], "in": at}
    if text:
        d["label"] = {"kicker": kicker or "", "text": text}
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


# ------------------------------------------------------------------ COLD OPEN
b("In [[1995|nineteen ninety-five]], a Canadian football team cut a young linebacker and sent him home with "
  "[[$7|seven dollars]] in his pocket.",
  stat("Calgary · 1995", 7, "in his pocket after he was cut", prefix="$", bg="mcmahon"))
b("He remembers looking in his wallet and finding a five, a one, and some change.",
  quote("A five, a one, and some change.", "Dwayne Johnson, to Esquire"))
b("Three years later, he was the champion of the [[WWF|W W F]].",
  tl(1995, 2002, 1995, 1998, "WWF Champion", "Three years"))
b("Seven years later, Hollywood paid him a record [[$5.5 million|five and a half million dollars]] for his first starring role.",
  stat("Seven years", 5.5, "for his first starring role", prefix="$", suffix="M", decimals=1,
       source="Guinness World Records", bg="universal"))
b("And almost three decades later, he sits on the board of the company that owns [[WWE|W W E]].",
  head("2024 · TKO", "From cut player to *board member*", bg="nyse"))
b("But the version of this story most people know skips the hard parts.",
  stmt("Most people know the *highlight reel*."))
b("The crowds that chanted for him to die. The years Hollywood kept him away. "
  "And the comeback that turned him into a villain at [[51|fifty-one]].",
  lst("The parts people skip", ["Crowds chanting for him to die", "Seven years away in Hollywood",
                                "A villain at 51"]))
b("This is the full story of Dwayne Johnson, The Rock. Where he came from, how he got famous, everything he won, "
  "how he walked away, and what he is doing right now, at the end of [[2026|twenty twenty-six]].",
  {"type": "title", "kicker": "The full story", "text": "The *Rock*", "sub": "1972 — 2026"}, pause=0.8)

# ------------------------------------------------------------------ 1
chapter(1, "Born into the business", "1972 — 1990")
b("Dwayne Douglas Johnson was born on [[May 2, 1972|May second, nineteen seventy-two]], in Hayward, California.",
  photo("hayward", "Hayward, California", "Born *May 2, 1972*"))
b("Wrestling was already the family job.", stmt("Wrestling was the *family job*.", bg="ring"))
b("His father, Rocky Johnson, was a star in the ring. In [[1983|nineteen eighty-three]], he and Tony Atlas "
  "won the [[WWF|W W F]] tag team titles, the first Black champions in the company's history.",
  head("1983 · Rocky Johnson", "First Black champions in *WWF history*", "with partner Tony Atlas"))
b("His mother's side was wrestling royalty too. His grandfather, High Chief Peter "
  "[[Maivia|Mye-vee-uh]], was a Samoan star.",
  head("His grandfather", "High Chief *Peter Maivia*", "a Samoan wrestling star"))
b("And his grandmother, Lia [[Maivia|Mye-vee-uh]], ran her own wrestling promotion in Hawaii in the "
  "[[1980s|nineteen-eighties]], one of the first women to do it.",
  head("Hawaii · 1982 — 1988", "His grandmother ran the *promotion*", "Polynesian Pacific Pro Wrestling"))
b("So Dwayne grew up around the business. He watched his father work, he watched crowds react, "
  "and he learned early that a wrestler's real job is to make people feel something.",
  photo("ring", "Raised around the ring", "A wrestler's job: make people *feel*"))
b("But a wrestler's life meant moving. A lot.",
  {"type": "map", "kicker": "A childhood on the move",
   "view": [-170, -55, 12, 50],
   "points": [["Hayward", 37.67, -122.08], ["Hamden", 41.40, -72.90], ["Honolulu", 21.31, -157.86],
              ["Nashville", 36.16, -86.78], ["Bethlehem", 40.63, -75.37]]})
b("Connecticut. A short stay with family in New Zealand. Then Honolulu, then Nashville, then Pennsylvania.")
b("In Honolulu, as a teenager, he came home to find an eviction notice on the family's door. "
  "He still talks about that day.",
  photo("waikiki", "Honolulu", "An *eviction notice* on the door"))
b("He was angry, and he got into trouble. By seventeen, he had been arrested several times, for fighting and theft.",
  stmt("By 17: arrested *several times*."))
b("Then, at Freedom High School in Pennsylvania, a football coach saw a big, angry kid "
  "and gave him somewhere to put it.",
  photo("bethlehem", "Bethlehem, Pennsylvania", "Freedom High *football*", fit="frame"))
b("Johnson has said football changed his life. By graduation in [[1990|nineteen ninety]], colleges were calling.",
  pause=0.8)

# ------------------------------------------------------------------ 2
chapter(2, "The Hurricane", "1990 — 1995")
b("The University of Miami gave him a full scholarship to play defensive tackle.",
  photo("umiami", "Miami · 1990", "A *full scholarship*", fit="frame"))
b("In [[1991|nineteen ninety-one]], the Hurricanes won the national championship, and Johnson was on that team.",
  head("1991", "National *champions*", "Miami Hurricanes", bg="orangebowl"))
b("But he was mostly a backup. Ahead of him on the depth chart was a future Hall of Famer, Warren Sapp.",
  head("The depth chart", "Behind *Warren Sapp*", "a future Pro Football Hall of Famer"))
b("In his college career, he played thirty-nine games, started one, and made four and a half sacks.",
  lst("College career", ["39 games", "1 start", "4.5 sacks", "77 tackles"]))
b("It was not the career he had pictured. He had planned on the [[NFL|N F L]].",
  stmt("The plan was the *NFL*."))
b("He finished his degree in [[1995|nineteen ninety-five]], went undrafted, "
  "and signed with the Calgary Stampeders of the Canadian Football League.",
  photo("mcmahon", "Calgary · 1995", "Undrafted. *Calgary* calls."), pause=0.8)

# ------------------------------------------------------------------ 3
chapter(3, "Seven bucks", "1995 — 1996")
b("Calgary put him on the practice roster and moved him to linebacker.",
  photo("calgary", "Calgary Stampeders", "Practice roster, *linebacker*"))
b("Two months into the season, they cut him.",
  head("1995", "Cut after *two months*", bg="mcmahon"))
b("He moved back in with his parents with seven dollars to his name, and he has said he fell into a depression.",
  stmt("*$7* to his name."))
b("Years later, he named his production company Seven Bucks, so he would never forget that moment.",
  head("Seven Bucks Productions", "Named after *that wallet*"))
b("But that low point forced a decision. He would do the one thing his family had always done.",
  stmt("He would *wrestle*.", bg="ring"))
b("He trained with his father, and later with Tom Prichard. Wrestling legend Pat Patterson got him tryout matches, "
  "and in [[March 1996|March nineteen ninety-six]], he beat The Brooklyn Brawler at a house show.",
  tl(1995, 1997, 1995.6, 1996.2, "WWF tryout win", "March 1996"))
b("Then he went to Memphis to learn the trade in front of small crowds, wrestling as Flex Kavana. "
  "He won the [[USWA|U S W A]] tag team titles twice, with Bart Sawyer.",
  photo("memphis", "Memphis · 1996", "Wrestling as *Flex Kavana*"))
b("By the fall, the [[WWF|W W F]] was ready to put him on its biggest stage.", pause=0.8)

# ------------------------------------------------------------------ 4
chapter(4, "Rocky Maivia", "1996 — 1997")
b("On [[November 17, 1996|November seventeenth, nineteen ninety-six]], at Survivor Series in Madison Square Garden, "
  "he wrestled his first big match.",
  photo("msg", "Survivor Series · 1996", "Debut at *Madison Square Garden*"))
b("The company called him Rocky [[Maivia|Mye-vee-uh]], his father's ring name joined to his grandfather's.",
  head("The name", "Rocky + *Maivia*", "his father's name and his grandfather's"))
b("He was the sole survivor of an eight-man elimination match. It looked like the start of an easy rise.",
  head("His first pay-per-view", "*Sole* survivor"))
b("Three months later, he beat Hunter Hearst Helmsley, the future Triple H, for the Intercontinental Championship.",
  vs("Rocky Maivia", "Hunter Hearst Helmsley", "Raw · Feb 13, 1997", "Maivia wins the Intercontinental title"))
b("And that is when it went wrong.", stmt("That's when it went *wrong*."))
b("The company sold him as a smiling, clean-cut good guy. But this was the late nineties. "
  "Fans wanted Stone Cold Steve Austin flipping off his boss, not a polite rookie with a big smile.",
  head("1997", "The wrong *era* for a nice guy"))
b("Crowds started chanting Rocky sucks. Some chanted die, Rocky, die.",
  quote("Die, Rocky, die.", "Arena chants, 1997"))
b("Then, in the summer of [[1997|nineteen ninety-seven]], he hurt his knee, and he was gone from television.",
  head("Summer 1997", "Knee injury. *Off TV.*"))
b("Most wrestlers in that spot fade away. He did the opposite. He listened to the boos.",
  stmt("He *listened* to the boos."), pause=0.8)

# ------------------------------------------------------------------ 5
chapter(5, "The Rock is born", "1997 — 1998")
b("When he came back in [[August 1997|August nineteen ninety-seven]], he joined the Nation of Domination, "
  "a group of villains, and he stopped fighting the crowd.",
  head("August 1997", "Joins the *Nation*", "and turns heel"))
b("He started talking about himself in the third person. He was not Rocky [[Maivia|Mye-vee-uh]] anymore. "
  "He was The Rock.",
  stmt("He was *The Rock.*"))
b("The insults, the raised eyebrow, the catchphrases. Fans who had booed the rookie now could not wait "
  "to hear what the villain would say next.",
  lst("The toolkit", ["Talking in the third person", "The People's Eyebrow", "Lines the crowd could finish"]))
b("A line like, if you smell what The Rock is cooking, only works when a whole arena says it with him. "
  "That was the trick. He made the crowd part of the act.",
  quote("If you smell what The Rock is cooking…", "The catchphrase"))
b("In [[December 1997|December nineteen ninety-seven]], he lost to Stone Cold at a pay-per-view, "
  "then took the Intercontinental title from him on Raw the next night.",
  vs("The Rock", "Stone Cold", "December 1997", "Rock takes the Intercontinental title on Raw"))
b("In [[1998|nineteen ninety-eight]], he took over the Nation and went to war with Triple H and D-Generation X.",
  head("1998", "Leader of the *Nation*", "vs. Triple H and D-Generation X"))
b("Triple H took the title from him in a ladder match at SummerSlam. But by then, The Rock was one of the most "
  "popular acts in the company, even as a villain.",
  vs("The Rock", "Triple H", "SummerSlam 1998", "Ladder match · Triple H wins the title"))
b("Then came Survivor Series, [[1998|nineteen ninety-eight]].", stmt("Survivor Series, *1998*.", bg="msg"))
b("The [[WWF|W W F]] held a tournament for its vacant championship. Rock fought through it as the crowd's favorite, "
  "beat Mankind in the final, and then turned on the fans.",
  head("Nov 15, 1998", "The *Deadly Game* tournament"))
b("Vince McMahon came out to celebrate with him. Rock was the boss's handpicked champion. The Corporate Champion.",
  head("The twist", "The *Corporate* Champion"))
b("It was his first [[WWF|W W F]] Championship. He was twenty-six, and the company's first world champion "
  "of African descent.",
  head("First world title", "*WWF Champion* at 26", "the company's first champion of African descent"))
b("Less than four years after Calgary sent him home.",
  tl(1995, 1999, 1995.6, 1998.9, "WWF Champion", "From $7"), pause=0.8)

# ------------------------------------------------------------------ 6
chapter(6, "The People's Champion", "1999 — 2000")
b("In [[January 1999|January nineteen ninety-nine]], he beat Mankind in an I Quit match to win the title back.",
  vs("The Rock", "Mankind", "Royal Rumble 1999", "'I Quit' match · Rock regains the title"))
b("Two months later came the first WrestleMania main event of the rivalry that defined the era. "
  "The Rock against Stone Cold Steve Austin, at WrestleMania [[XV|fifteen]] in Philadelphia.",
  photo("wellsfargo", "WrestleMania XV · Philadelphia", "Rock vs. *Stone Cold*, part one"))
b("Austin won. But something was changing. Fans had started cheering The Rock, "
  "even when he was supposed to be the bad guy.",
  vs("The Rock", "Stone Cold", "WrestleMania XV · 1999", "Austin wins the WWF title"))
b("By late [[1999|nineteen ninety-nine]], he was a full good guy, the People's Champion. "
  "He even teamed with Mankind, the man he had just been fighting, as the Rock 'n' Sock Connection.",
  head("The Rock 'n' Sock Connection", "*Three* tag team titles", "with Mankind"))
b("On [[September 27, 1999|September twenty-seventh, nineteen ninety-nine]], Mankind threw him a This Is Your Life "
  "party on Raw. He brought out an old teacher, his football coach and his high school sweetheart, "
  "and The Rock spent the segment trying not to laugh, and failing.",
  head("Raw · Sep 27, 1999", "*This Is Your Life*", "Mankind's tribute to The Rock"))
b("You will often hear it was the highest-rated segment in Raw history. It was not. "
  "It drew an [[8.4|eight point four]] rating, which is huge.",
  stat("Quarter-hour rating", 8.4, "huge — but not Raw's record", decimals=1))
b("But a Stone Cold title match that summer drew a [[9.5|nine point five]].",
  stat("June 1999", 9.5, "Austin vs. The Undertaker — the real record", decimals=1))
b("What the segment did prove was this. He could do comedy. Hollywood noticed.",
  stmt("Hollywood *noticed*.", bg="hollywood_sign"))
b("In [[2000|two thousand]], he hosted Saturday Night Live, and his autobiography, The Rock Says, "
  "became a New York Times bestseller.",
  lst("2000", ["Hosts Saturday Night Live", "'The Rock Says…' — a bestseller", "Wins the Royal Rumble"]))
b("He also won the Royal Rumble that year, although replays suggested his feet touched the floor first. "
  "Big Show protested, and beat him at the next pay-per-view.",
  head("Royal Rumble 2000", "A *disputed* win", "Big Show beat him a month later"))
b("Rock still reached WrestleMania, in a four-way main event that Triple H won. "
  "Then, at Backlash, he finally beat Triple H for the title.",
  vs("The Rock", "Triple H", "Backlash 2000", "Rock wins the WWF title"))
b("By the summer of [[2000|two thousand]], he was a five-time world champion, "
  "and with Austin, one of the two biggest stars in the business.",
  stat("June 2000", 5, "world title reigns — already", suffix="×"), pause=0.8)

# ------------------------------------------------------------------ 7
chapter(7, "Hollywood calls", "2001 — 2004")
b("In [[2001|two thousand one]], he appeared in The Mummy Returns as the Scorpion King. "
  "Universal liked him so much that it gave the character his own movie.",
  photo("universal", "2001", "*The Mummy Returns*"))
b("Wrestling still came first, though. At WrestleMania [[X-Seven|ex seven]], he and Austin met again, "
  "in front of [[67,925|sixty-seven thousand, nine hundred and twenty-five]] people at the Houston Astrodome.",
  photo("astrodome", "WrestleMania X-Seven · Houston", "*67,925* in the Astrodome"))
b("Austin won again, after shaking hands with Vince McMahon, his worst enemy. "
  "It became the most-bought pay-per-view the company had ever sold in North America.",
  vs("The Rock", "Stone Cold", "WrestleMania X-Seven · 2001", "Austin wins · and joins McMahon"))
b("Then came the paycheck. For [[2002|two thousand two]]'s The Scorpion King, Universal paid him "
  "[[$5.5 million|five and a half million dollars]]. Guinness World Records lists it as the highest salary ever "
  "for a first starring role.",
  stat("The Scorpion King · 2002", 5.5, "highest pay for a debut starring role", prefix="$", suffix="M",
       decimals=1, source="Guinness World Records", bg="projector"))
b("A month before that movie came out, he had the match many fans remember most. "
  "WrestleMania [[X8|ex eight]], in Toronto. The Rock against Hulk Hogan.",
  vs("The Rock", "Hulk Hogan", "WrestleMania X8 · Toronto", "Icon vs. Icon", bg="cntower"))
b("Hogan was supposed to be the villain. [[68,237|Sixty-eight thousand, two hundred and thirty-seven]] fans "
  "at the SkyDome cheered him anyway, and Rock adjusted in the middle of the match, "
  "playing off the crowd instead of fighting it.",
  photo("cntower", "SkyDome · Toronto", "*68,237* fans cheered the villain"))
b("Rock won. Then he shook Hogan's hand and helped him fight off his old friends.")
b("In July, he won the Undisputed Championship, a record seventh world title at the time. "
  "In August, he lost it to a twenty-five-year-old named Brock Lesnar.",
  vs("The Rock", "Brock Lesnar", "SummerSlam 2002", "Lesnar wins the Undisputed title"))
b("Rock was heading back to Hollywood, and the company used him to make its next star.",
  stmt("Passing the *torch*.", bg="hollywood_sign"))
b("Fans took it personally. When he came back in [[2003|two thousand three]], they booed him, "
  "so he became Hollywood Rock, a smug movie star who mocked the cities he visited.",
  head("2003", "*Hollywood* Rock", "the crowd booed, so he leaned in"))
b("At WrestleMania [[XIX|nineteen]] in Seattle, he finally beat Stone Cold. It turned out to be Austin's last match.",
  photo("safeco", "WrestleMania XIX · Seattle", "Rock beats Austin. *Austin's last match.*"))
b("A year later, at WrestleMania [[XX|twenty]] in Madison Square Garden, he and Mick Foley lost a handicap match "
  "to Evolution. Then his contract ran out in [[2004|two thousand four]], and he was gone.",
  head("August 2004", "Contract *over*", "his last match for seven years", bg="msg"), pause=0.8)

# ------------------------------------------------------------------ 8
chapter(8, "Finally", "2004 — 2016")
b("For seven years, wrestling barely saw him. He made Walking Tall, Gridiron Gang, The Game Plan, Tooth Fairy. "
  "Some hits, some misses.",
  lst("2004 — 2010", ["Walking Tall", "Gridiron Gang", "The Game Plan", "Tooth Fairy"], bg="theater"))
b("A lot of fans felt he had turned his back on the business.",
  stmt("Fans felt *left behind*."))
b("Then, on [[February 14, 2011|February fourteenth, twenty eleven]], his music hit on Raw, "
  "and the building lost it. Finally, he said, The Rock has come back.",
  head("Raw · Feb 14, 2011", "Finally, The Rock has come *back*"))
b("Two months later, at WrestleMania in Atlanta, he cost John Cena the title. "
  "The next night, they agreed to face each other a full year later, in Miami.",
  photo("georgiadome", "WrestleMania XXVII · Atlanta", "Rock costs Cena the *title*"))
b("They called it Once in a Lifetime.",
  vs("The Rock", "John Cena", "Announced April 2011", "WrestleMania XXVIII · Miami · one year away"))
b("That same spring, Fast Five came out. He played Luke Hobbs, and the franchise got bigger than ever.",
  head("2011", "Fast Five: *Luke Hobbs*", bg="theater"))
b("On [[April 1, 2012|April first, twenty twelve]], in front of "
  "[[78,363|seventy-eight thousand, three hundred and sixty-three]] fans in Miami, he pinned Cena in his college town.",
  photo("hardrock", "WrestleMania XXVIII · Miami", "*78,363* in his college town"))
b("It is still listed as the most-bought wrestling pay-per-view of all time.",
  head("The record", "The *most-bought* wrestling pay-per-view ever"))
b("In [[January 2013|January twenty thirteen]], he beat CM Punk at the Royal Rumble for the [[WWE|W W E]] Championship. "
  "Seventy days later, at WrestleMania [[29|twenty-nine]], he lost it to Cena. Twice in a lifetime.",
  vs("The Rock", "CM Punk", "Royal Rumble 2013", "Rock wins the WWE title · lost it 70 days later", bg="metlife"))
b("Meanwhile, Hollywood was going all in on him.", stmt("Hollywood went *all in*.", bg="hollywood_sign"))
b("Forbes named him the world's highest-paid actor in [[2016|twenty sixteen]], "
  "with an estimated [[$64.5 million|sixty-four and a half million dollars]].",
  stat("Forbes · 2016", 64.5, "world's highest-paid actor", prefix="$", suffix="M", decimals=1, source="Forbes"))
b("That year he also voiced Maui in Moana. And at WrestleMania [[32|thirty-two]], "
  "he beat Erick Rowan in six seconds, the fastest win in WrestleMania history.",
  stat("WrestleMania 32 · 2016", 6, "vs. Erick Rowan — the fastest win in WrestleMania history",
       suffix=" sec", bg="cowboys"))
b("Then he stopped wrestling altogether.", stmt("Then he *stopped*."), pause=0.8)

# ------------------------------------------------------------------ 9
chapter(9, "Walking away", "2017 — 2023")
b("Jumanji, Welcome to the Jungle made more than [[$960 million|nine hundred and sixty million dollars]] "
  "worldwide, and its sequel made about eight hundred million more.",
  {"type": "bars", "kicker": "Box office, worldwide", "title": "Jumanji",
   "items": [["Welcome to the Jungle (2017)", 962, "$962M"], ["The Next Level (2019)", 801.7, "$802M"]]})
b("Forbes put him back at number one in [[2019|twenty nineteen]], and again in [[2020|twenty twenty]].",
  lst("Forbes: world's highest-paid actor", ["2016 — $64.5M", "2019 — $89.4M", "2020 — $87.5M"]))
b("On [[August 3, 2019|August third, twenty nineteen]], he said he was officially retired from professional wrestling.",
  head("Aug 3, 2019", "Officially *retired*"))
b("Two months later, he still showed up for SmackDown's first night on Fox, and dropped a People's Elbow in the ring.",
  head("Oct 4, 2019", "One more *People's Elbow*", "SmackDown's debut on Fox"))
b("In [[January 2020|January twenty twenty]], his father, Rocky Johnson, passed away.",
  head("January 2020", "Rocky *Johnson*", "1944 — 2020"))
b("That August, he, his business partner and ex-wife Dany Garcia, and RedBird Capital bought the "
  "[[XFL|X F L]] for [[$15 million|fifteen million dollars]], hours before it was due to go to auction.",
  stat("August 2020 · XFL", 15, "bought out of bankruptcy, with Dany Garcia and RedBird", prefix="$", suffix="M",
       source="Reuters"))
b("He built a tequila brand, an energy drink and a training line with Under Armour. "
  "He was busier than ever. He just was not wrestling.",
  lst("The business", ["Seven Bucks Productions", "Teremana Tequila", "ZOA Energy", "Project Rock · Under Armour"]))
b("Then, in [[September 2023|September twenty twenty-three]], in Denver, his music hit on SmackDown "
  "for the first time in four years. He insulted Austin Theory, hit him with a People's Elbow, and [[WWE|W W E]] said "
  "the clips drew more than [[103 million|a hundred and three million]] views on social media.",
  stat("Denver · Sep 15, 2023", 103, "social views of his surprise return", suffix="M+", source="WWE"), pause=0.8)

# ------------------------------------------------------------------ 10
chapter(10, "The Final Boss", "2024 — 2025")
b("On [[January 23, 2024|January twenty-third, twenty twenty-four]], [[TKO|T K O]], the company that owns "
  "[[WWE|W W E]] and the [[UFC|U F C]], put Dwayne Johnson on its board of directors.",
  photo("nyse", "Jan 23, 2024 · TKO", "A seat on the *board*"))
b("As part of the deal, he got something he had never had. Full ownership of the name, The Rock.",
  head("The trademark", "He finally owns *'The Rock'*"))
b("Then he did something nobody expected from a fifty-one-year-old movie star. He turned heel.",
  stmt("At 51, he turned *heel*."))
b("At a press event in Las Vegas, he slapped Cody Rhodes, and sided with his family member Roman Reigns.",
  head("Feb 2024 · Las Vegas", "The *slap*", "Rock sides with Roman Reigns", bg="vegas_pano"))
b("He called himself The Final Boss. A villain built from everything fans had loved and hated about him. "
  "The swagger of the People's Champion, and the arrogance of Hollywood Rock.",
  head("The new character", "The *Final Boss*"))
b("At WrestleMania [[XL|forty]] in Philadelphia, he teamed with Reigns to beat Cody Rhodes and Seth Rollins. "
  "It was his first match in eight years.",
  photo("linc", "WrestleMania XL · Philadelphia", "His first match in *8 years*", fit="frame"))
b("The next night, Cody beat Reigns anyway, and the story of The Rock against Cody was saved for later.",
  vs("Rock & Reigns", "Rhodes & Rollins", "WrestleMania XL · Night 1", "Rock and Reigns win · Cody wins night 2"))
b("Rock came back at Bad Blood in October, and again for Raw's first night on Netflix, "
  "in [[January 2025|January twenty twenty-five]].",
  tl(2024, 2026, 2024.75, 2025.02, "Bad Blood · Raw on Netflix", "Oct 2024 → Jan 2025"))
b("In February, in New Orleans, he made Cody an offer. Become my champion. Give me your soul.",
  photo("superdome", "SmackDown · New Orleans", "He wanted Cody's *soul*"))
b("At Elimination Chamber in Toronto, Cody said no. So John Cena, the man Rock had faced twice at WrestleMania, "
  "turned heel, attacked Cody, and sold his soul to The Rock instead.",
  video("toronto_video", 4, "Elimination Chamber · Toronto", "Cena sells his *soul*"))
b("It was one of the most shocking turns in years. And then The Rock disappeared.",
  stmt("Then he *disappeared*."))
b("He was not at WrestleMania [[41|forty-one]]. He was not at WrestleMania [[42|forty-two]] in Las Vegas this April "
  "either. As far as [[WWE|W W E]] television goes, Elimination Chamber, [[2025|twenty twenty-five]], "
  "is still the last time we saw him.",
  head("Last seen on WWE TV", "*March 1, 2025*", "Elimination Chamber · Toronto", bg="vegas_pano"), pause=0.8)

# ------------------------------------------------------------------ 11
chapter(11, "Where is he now?", "2025 — 2026")
b("Mostly, he has been chasing something box office records never gave him. Respect as an actor.",
  stmt("Chasing *respect* as an actor.", bg="theater"))
b("In The Smashing Machine, he played the [[MMA|M M A]] fighter Mark Kerr, under heavy prosthetics, "
  "for the director Benny Safdie and the studio [[A24|A twenty-four]].",
  head("The Smashing Machine · 2025", "Playing *Mark Kerr*", "directed by Benny Safdie for A24"))
b("It premiered at the Venice Film Festival, where Safdie won the Silver Lion for best director, "
  "and Johnson went on to earn his first Golden Globe nomination.",
  photo("venice", "Venice · 2025", "*Silver Lion* for Safdie", fit="frame"))
b("But it made only around [[$20 million|twenty million dollars]] worldwide, on a "
  "[[$50 million|fifty million dollar]] budget. And in January, the Oscars passed him over for Best Actor.",
  {"type": "bars", "kicker": "The Smashing Machine", "title": "Budget vs. box office",
   "items": [["Budget", 50, "$50M"], ["Worldwide gross", 20, "≈ $20M"]]})
b("He said the snub lit a fire in his spine.",
  quote("It lit a fire in my spine.", "Dwayne Johnson, 2026"))
b("This July, he was back as Maui, in Disney's live-action Moana. It opened at number one with "
  "[[$43 million|forty-three million dollars]], well below Disney's recent remakes.",
  stat("Moana · July 2026", 43, "No. 1 opening weekend, US & Canada", prefix="$", suffix="M",
       source="Box Office Mojo", bg="theater"))
b("It finished with about [[$324 million|three hundred and twenty-four million dollars]] worldwide. "
  "But when it reached Disney Plus in October, it went straight to the top of the charts.",
  head("October 2026", "No. 1 on *Disney+*", "after a soft run in theaters"))
b("Next up is Jumanji, Open World, in theaters on Christmas Day. And right now, he is in New York filming "
  "Lizard Music, his second movie with Benny Safdie, playing an eccentric old man the film calls the Chicken Man.",
  lst("Coming up", ["Jumanji: Open World — Dec 25, 2026", "Lizard Music — filming in New York"],
      bg="nyc_video"))
b("Photos from the set show him with gray hair, a scraggly beard and a floppy hat. Unrecognizable.",
  stmt("Gray hair. Floppy hat. *Unrecognizable.*"))
b("Off screen, he was re-elected to [[TKO|T K O]]'s board in June, he still co-owns the [[UFL|U F L]], "
  "and he still runs Seven Bucks.",
  lst("Off screen", ["TKO board — re-elected June 2026", "Co-owner of the UFL", "Seven Bucks Companies"],
      bg="nyse"))
b("And in January, his daughter Simone, who wrestled as Ava, chose not to renew her [[WWE|W W E]] contract, "
  "after six years with the company.",
  head("January 2026", "*Ava* leaves WWE", "his daughter, after six years"))
b("So, is The Rock done with wrestling?", stmt("Is he *done*?"))
b("He has not said so. In August, he told the hosts of The Morning Shift they would be his special guests "
  "whenever he goes back to WrestleMania.",
  quote("Whenever I do go back to WrestleMania…", "The Rock, August 2026"))
b("WrestleMania [[43|forty-three]] will be held in Saudi Arabia in [[2027|twenty twenty-seven]], the first one "
  "outside North America, and wrestling reporters keep linking him to it, possibly against Cody Rhodes or Roman "
  "Reigns. For now, that is a rumor, not a booking.",
  head("WrestleMania 43 · Saudi Arabia · 2027", "A rumor, *not a booking*"), pause=0.8)

# ------------------------------------------------------------------ 12
chapter(12, "The legacy", "By the numbers")
b("Here is what he left in the ring. Ten world championships. Two Intercontinental titles. Five tag team titles. "
  "The [[2000|two thousand]] Royal Rumble. And the company's sixth Triple Crown champion.",
  lst("Career", ["10× world champion", "2× Intercontinental champion", "5× tag team champion",
                 "2000 Royal Rumble winner", "6th Triple Crown champion"]))
b("He main-evented WrestleMania six times, and headlined the most-bought pay-per-view in wrestling history.",
  stat("WrestleMania", 6, "main events", suffix="×", bg="cowboys"))
b("But the numbers are not why he matters.", stmt("The numbers aren't the *point*."))
b("He proved that the skills a wrestler learns, reading a crowd, timing a line, making people feel something, "
  "could carry a man all the way to the top of Hollywood. Everyone who has tried that jump since "
  "gets measured against him.",
  photo("star", "Hollywood Walk of Fame", "The *blueprint*"))
b("And it all started with a crowd chanting for him to die, and a kid with seven dollars in his wallet.",
  stat("Where it started", 7, "and a crowd that wanted him gone", prefix="$", bg="mcmahon"), pause=0.6)
b("Stone Cold Steve Austin's story is next on this channel. Subscribe, so you do not miss it.",
  {"type": "end", "kicker": "Next on the channel", "text": "Stone Cold: the *full story*",
   "cta": "Subscribe", "follow": "New WWE stories every week"})
b("And tell me in the comments, which Rock match is the greatest of all time?",
  {"type": "end", "kicker": "Your take", "text": "The greatest Rock match *ever?*",
   "cta": "Tell us below ↓", "follow": "Subscribe for the next story"})

# ------------------------------------------------------------------ real footage slots (files Ayaz saves as R01.jpg, R15.mp4 ...)
SLOTMAP = {0: "R01", 1: "R01", 2: "R02", 3: "R03", 4: "R04", 5: "R59", 6: "R17", 7: "R60",
           10: "R06", 11: "R07", 12: "R08", 13: "R08", 14: "R06",
           22: "R11", 23: "R11", 24: "R11", 25: "R11", 26: "R11", 27: "R01",
           29: "R01", 30: "R01", 31: "R01", 32: "R13", 33: "R13", 34: "R13", 35: "R14",
           38: "R15", 39: "R15", 40: "R15", 41: "R16", 42: "R17", 43: "R17", 44: "R17", 45: "R18", 46: "R18",
           48: "R18", 49: "R18", 50: "R59", 51: "R59", 52: "R19", 53: "R20", 54: "R20", 55: "R02", 56: "R02",
           57: "R21", 58: "R21", 59: "R21",
           61: "R22", 62: "R23", 63: "R23", 64: "R24", 65: "R25", 66: "R25", 68: "R26", 69: "R26", 70: "R27",
           71: "R27", 72: "R59",
           74: "R03", 75: "R23", 76: "R29", 77: "R03", 78: "R30", 79: "R30", 81: "R31", 82: "R31", 83: "R32",
           84: "R23", 85: "R34",
           87: "R36", 89: "R35", 90: "R35", 91: "R37", 92: "R36", 93: "R37", 94: "R37", 95: "R38", 96: "R39",
           97: "R42", 98: "R40", 99: "R40",
           101: "R41", 102: "R41", 103: "R43", 104: "R43", 105: "R09", 107: "R42", 108: "R45",
           110: "R04", 111: "R04", 112: "R05", 113: "R05", 114: "R50", 115: "R48", 116: "R48", 117: "R49",
           118: "R51", 119: "R52", 120: "R52",
           123: "R53", 124: "R53", 125: "R54", 126: "R53", 127: "R54", 128: "R55", 129: "R55", 130: "R56",
           131: "R57", 132: "R04", 134: "R59",
           138: "R59", 139: "R59", 140: "R59", 141: "R42", 142: "R01"}
for i, slot in SLOTMAP.items():
    assert "show" in B[i], i
    B[i]["show"]["slot"] = slot

# on-screen credit per slot (the source of the clip/photo)
SLOT_CREDIT = {s: "WWE" for s in ("R02", "R06", "R07", "R08", "R09", "R13", "R14", "R15", "R16", "R17", "R18",
                                   "R19", "R20", "R21", "R22", "R23", "R24", "R25", "R27", "R29", "R30", "R31",
                                   "R32", "R34", "R35", "R37", "R38", "R40", "R43", "R45", "R48", "R49", "R50",
                                   "R51", "R52", "R59")}
SLOT_CREDIT.update({"R01": "Calgary Stampeders", "R03": "Universal Pictures", "R04": "NYSE / TKO",
                    "R05": "WWE", "R11": "University of Miami / Getty Images", "R26": "NBC / SNL",
                    "R36": "Universal Pictures", "R39": "Disney", "R41": "Sony Pictures", "R42": "Variety",
                    "R53": "A24", "R54": "Venice Film Festival", "R55": "Disney", "R56": "Sony Pictures",
                    "R57": "TMZ / E! News", "R60": ""})

job = {
    "id": "2026-11-02-the-rock",
    "format": "longform",
    "title": "The Rock: From $7 in His Pocket to WWE Legend | Full Story",
    "voice": {"tts": "kokoro", "voice": "am_michael", "speed": 1.03},
    "music": {"gen": "ambient", "gain_db": -24},
    "thumbnail": {"kicker": "The full story", "text": "The *Rock*", "sub": "From *$7* to legend", "slot": "R60",
                  "sharp": True, "focus": [0.5, 0.22], "big": "$7"},
    "slot_credit": SLOT_CREDIT,
    "slot_in": {},
    "beats": B,
}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-02-the-rock.json")
json.dump(job, open(out, "w"), ensure_ascii=False, indent=1)
words = sum(len(x["say"].split()) for x in B)
print(f"{len(B)} beats, ~{words} words (raw), scenes: {sum(1 for x in B if 'show' in x)}")
