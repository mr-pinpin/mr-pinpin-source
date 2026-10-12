"""Explicit beat/continuity/register plan; no artwork or publication implied."""
import json,hashlib
from pathlib import Path
p=Path(__file__).resolve().parent;root=p.parents[3]
# Each row is a single playable visual turn, not a caption quota.
days=[
[
('Warm kitchen','H1','Mama Papa PinPin PomPom','Family morning; Papa supports the infant while Mama prepares porridge.'),
('Four bowls','H1','Mama Papa PinPin PomPom','Set exactly four family bowls and spoons, with warm bread in the middle.'),
('Bread exchange','H1','Papa PinPin PomPom Mama','Papa passes bread with his free paw while his other forearm supports PomPom.'),
('Tiny spoon reply','H1','Mama Papa PinPin PomPom','PomPom taps his spoon from Papa\'s supported lap; Mama answers the tap.'),
('Cleanup and handover','H1','Papa Mama PinPin PomPom','PinPin gathers bowls; Papa visibly settles PomPom into Mama\'s supported arms.'),
('Ball rolls','H1','Mama PinPin PomPom','Mama rolls the familiar soft ball with her free paw while holding PomPom.'),
('Infant touches ball','H1','Mama PinPin PomPom','PinPin brings the ball close; supported PomPom touches it, then it rolls back.'),
('Papa announces walk','H1','Papa Mama PinPin PomPom','Papa tells the family he is taking Scooby for a walk and practice; child stays home for now.'),
('Scooby at the step','H0','Papa Scooby','Dog\'s separate breakfast bowl is empty; Papa greets him at the familiar doorway.'),
('Sit cue','H0','Papa Scooby','Papa gives the cue and Scooby actually sits; focused eye contact and grounded paws.'),
('Watch the hand','H0','Papa Scooby','Hold the attention beat: Papa\'s quiet hand and Scooby\'s alert ears, not a second treat.'),
('Wait cue','H0','Papa Scooby','Papa takes one small step away; Scooby holds the sit and watches.'),
('Release and walk','F0','Papa Scooby','Papa releases the wait; they move onto the shown forest path.'),
('Mama\'s small care','H1','Mama PomPom PinPin','Meanwhile Mama gently wipes the baby\'s cheek with the infant cloth; child watches.'),
('Knock','H0','Mama PomPom PinPin','A knock turns PinPin\'s head; Mama keeps the infant supported.'),
('Rabbit on the step','H0','Rabbit PinPin Mama PomPom','Introduce canonical Rabbit carrying exactly two folded green leaf boats.'),
('Invitation','H0','Rabbit PinPin','Rabbit asks to play by the spring; child listens instead of immediately running away.'),
('Permission and route','H0','Mama PomPom PinPin Rabbit','Mama agrees to the short outing; name the spring route and returning path.'),
('Children take the fork','F0','PinPin Rabbit','Wide geography: children take the spring side, each carrying one of the two leaves.'),
('Papa takes forest side','F0','Papa Scooby','Same fork and landmarks; Papa and dog continue on the other side.'),
('Window wave','H1','Mama PomPom','Mama and supported PomPom give the outing a brief domestic counterbeat.'),
('Nose catches a scent','F1','Papa Scooby','Dog slows at a fern/root glade; mouth closed, scent-focused posture.'),
('Papa notices','F1','Papa Scooby','Papa follows the dog\'s eyeline and stops; he is attentive, not grinning.'),
('Cool draft and petal','F1','Papa Scooby','A cool draft moves one unusual fallen petal beside an old root-covered hollow.'),
('Loose litter moves','F1','Papa Scooby','Scooby scrapes loose leaves/soil from the natural hollow; incidental mud begins on forepaws.'),
('An entrance','C0','Papa Scooby','Reveal an existing broad root tunnel mouth; no deep excavation or trapped dog.'),
('Wait at threshold','C0','Papa Scooby','Papa uses the practiced wait; dog stops while he looks at the entrance.'),
('Check the first ground','C0','Papa Scooby','Papa examines firm visible ground and the daylight lip before anyone enters.'),
('Spring established','S0','PinPin Rabbit','Children arrive by the known stone spring; the two canonical birds are visible.'),
('Bird greeting','S0','PinPin Rabbit BlueTit Robin','A small greeting/reaction ties this spring to the prior chapter.'),
('Adjust leaf edges','S0','PinPin Rabbit','Each child adjusts his existing leaf boat; no additional leaves appear.'),
('First leaf released','S0','PinPin Rabbit','One boat glides along the current; hands/ownership are visible.'),
('Second turns','S0','PinPin Rabbit','The second circles in a little eddy; children notice the difference.'),
('Bird watches the turn','S0','BlueTit Robin PinPin Rabbit','A quiet bird reaction lets the observation breathe, with differing eyelines.'),
('A call from the path','S0','PinPin Rabbit','Children hear Papa\'s ordinary call, retrieve both boats and turn toward the shown return route.'),
('Return through fork','F0','PinPin Rabbit','Show the actual crossing from spring side toward fern/root glade.'),
('Paths rejoin','F1','Papa Scooby PinPin Rabbit','The groups meet; no child teleports into the original dog walk.'),
('Papa explains draft','F1','Papa Scooby PinPin Rabbit','Papa points to the petal and moving ferns; children listen.'),
('PinPin looks closely','C0','Papa Scooby PinPin Rabbit','Child studies the unusual petal/root opening, not another arbitrary treasure.'),
('One petal taken','C0','Papa Scooby PinPin Rabbit','PinPin picks up that same fallen petal as a small reminder; route remains visible.'),
('First chamber glimpse','C1','Papa Scooby PinPin Rabbit','From the bright entrance lip, reveal moss/vines/pool reflections and warm berry glow.'),
('A small echo','C1','Papa Scooby PinPin Rabbit','Papa\'s quiet word returns as an echo; faces listen rather than cheer.'),
('Meanwhile at home','H1','Mama PomPom','Mama steadies PomPom as he reaches for his cloth; retain the household thread.'),
('Come prepared tomorrow','C0','Papa Scooby PinPin Rabbit','Papa decides on a prepared family return; the first look ends deliberately.'),
('Remember the birch','F1','Papa Scooby PinPin Rabbit','Show the forked birch/root landmarks they will recognise tomorrow; no spawned trail equipment.'),
('Homeward path','F0','Papa Scooby PinPin Rabbit','Walk home; leaf boats and petal are carried by their named holders.'),
('Rabbit\'s farewell','H0','Rabbit PinPin Papa Scooby','Return both leaves to Rabbit and close today\'s invitation; agree to meet tomorrow.'),
('Tell Mama','H1','Mama PomPom Papa PinPin','Family hears the discovery; the single petal is put on a small cloth by the table.'),
('Wipe dog paws','H0','Papa Scooby','Clean the day\'s incidental soil with the separate sage dog cloth before entering.'),
('Rinse the used cloth','H1','Papa Mama PomPom PinPin','Account for the soiled cloth and simple evening cleanup; it never wipes the infant.'),
('Family settles','H2','Mama Papa PinPin PomPom','Four family hedgehogs in the familiar broad bed; supported infant, quiet expressions.'),
('Scooby rests','H1','Scooby','Dog lies on his existing cushion; day closes, no magic water source has been created.')
],
[
('New morning','H2','Mama Papa PinPin PomPom','Open day2 clearly; no unexplained continuous twenty-hour outing.'),
('Discovery remembered','H1','Mama Papa PinPin PomPom','Breakfast talk returns to the petal and echo with alert, curious faces.'),
('Picnic cloth packed','H1','Mama PomPom PinPin','Mama packs the known picnic cloth and food while supporting PomPom.'),
('Flask and dog bowl','H1','Papa PinPin','Papa fills the flask and nests cups/dog bowl in the bag.'),
('Three marker strips','H1','Papa PinPin','Introduce exactly three small ochre route strips; pack them visibly.'),
('Check the bag','H0','Mama PomPom Papa PinPin Scooby','Assign bag/petal holders and confirm items before departure.'),
('Rabbit returns','H0','Rabbit PinPin Papa Scooby','Rabbit brings the same two leaves kept damp overnight; confirm this continuity.'),
('Leaf condition','H0','PinPin Rabbit','Children inspect/adjust the two actual leaves; no sudden third boat.'),
('Scooby lowers','H0','Papa Scooby Mama PomPom','Dog lowers/sits; parents prepare the supported infant/mother mounting handover.'),
('Infant handover for mounting','H0','Papa Mama PomPom Scooby','Papa supports PomPom while Mama settles onto Scooby; no unsupported baby or extra arms.'),
('PomPom back to Mama','H0','Papa Mama PomPom Scooby','Papa returns the infant into securely supported Mama arms; one adult plus infant rides.'),
('Gentle family departure','F0','Papa Mama PomPom PinPin Rabbit Scooby','Papa/children walk beside mother/infant\'s slow ride; named capacities and holders.'),
('Fork recognised','F0','Papa Mama PomPom PinPin Rabbit Scooby','Use the same route landmarks from yesterday.'),
('Birch landmark','F1','Papa Mama PomPom PinPin Rabbit Scooby','The forked birch and root glade confirm location.'),
('Wait and dismount','C0','Papa Mama PomPom Scooby','Wait cue pays off; supported dismount occurs before cave ground.'),
('First route strip','C0','Papa PinPin Rabbit','Tie marker1 at a visible root near entrance; it is directional, not a magic sign.'),
('Petal returned','C0','Mama PomPom PinPin','Show supported PomPom touching the single petal before it is returned to native moss.'),
('C1 wide','C1','Papa Mama PomPom PinPin Rabbit Scooby','Establish broad daylight lobby and route before closer action.'),
('Fern attention','C1','Mama PomPom PinPin','Mother supports a curious infant reaching toward an actual fern edge.'),
('Paws stay on path','C1','Papa Scooby','Papa guides dog along the visible firm root path; natural mild soil/wet paws.'),
('Listen to drops','C1','PinPin Rabbit','Children stop to listen, with closed mouths and distinct ear/brow responses.'),
('Glowberry gallery first view','C2','Papa PinPin Rabbit Scooby','Show connection from lobby and warm hanging berry lights, not a new unrelated cave.'),
('Light on faces','C2','Papa PinPin Rabbit Scooby','Quiet awe; maintain cast identity/skin colours in ambient light.'),
('Mother\'s daylight station','C1','Mama PomPom','Crosscut explains where supported infant/mother remain while the scout group looks ahead.'),
('Back for family','C1','Papa PinPin Rabbit Scooby Mama PomPom','Scout group returns by the shown connection; share the observation.'),
('Picnic cloth unfolds','C1','Mama Papa PinPin PomPom Rabbit','Use packed cloth at broad sunlit station; holders/infant support remain possible.'),
('Food placed','C1','Mama Papa PinPin PomPom Rabbit Scooby','Bring out only packed food/cups and dog bowl.'),
('PomPom\'s small meal','C1','Mama PomPom','Supported infant receives a quiet feeding beat; no free-standing toddler.'),
('Scooby drinks','C1','Papa Scooby','Use the packed dog bowl, then set it back beside cloth.'),
('Children recount glow','C1','PinPin Rabbit Papa','Small disagreement/question about light, not universal delighted grin.'),
('Elder arrives by entrance','C0','Elder Papa PinPin Rabbit','Established mentor joins by visible route; no unexplained cave apparition.'),
('Tell Elder','C1','Elder Papa Mama PomPom PinPin Rabbit','Family offers observations rather than being handed the answer.'),
('Elder\'s clue','C1','Elder PinPin Rabbit Papa','One limited observation about roots/water/echo; wry attentive register.'),
('A small paper map','C1','Elder Papa PinPin Rabbit','Introduce one map sheet/pencil explicitly on picnic cloth.'),
('Draw what we saw','C1','PinPin Rabbit Elder','Children mark actual seen chambers; no completed map of unseen system.'),
('Echo pool approached','C3','Papa PinPin Rabbit Scooby','Show connection, broad firm bank and pool orientation.'),
('A spoken word returns','C3','Papa PinPin Rabbit','Try one quiet word and listen; no monster or magical speaking stone.'),
('Mother/infant at broad lip','C3','Mama PomPom Papa','Bring supported pair via the visible broad route, not a deep crossing.'),
('PomPom\'s echo','C3','Mama PomPom PinPin Rabbit','Infant\'s small sound returns; earned brief surprise/pleasure.'),
('Pause after echo','C3','Mama PomPom Papa PinPin Rabbit','Allow genuine varied reactions; not all faces copy the infant\'s grin.'),
('Two branches seen','C4','Papa PinPin Rabbit Scooby','Establish fork and stream directions from the echo-pool connection.'),
('Mark second root','C4','Papa PinPin Rabbit','Tie marker2 at chosen fork; leave other branch for later.'),
('Flowers beyond','C5','Papa PinPin Rabbit Scooby','A linked glimpse of blossom room, warm moss and reflected light.'),
('Observe without picking','C5','PinPin Rabbit Papa','Interest in flowers, not a new inventory of unexplained treasures.'),
('Scooby checks ground','C5','Papa Scooby','Useful nose/attention beat; paws get damp, coat does not become heavily muddy yet.'),
('Turn back deliberately','C4','Papa PinPin Rabbit Scooby','Use marker/connection and explicit decision to return.'),
('Collect picnic items','C1','Mama Papa PinPin PomPom Rabbit','Count cups/flask/cloth/bowl; pack what was brought.'),
('Map into bag','C1','Papa PinPin Elder','Keep one map; mentor\'s participation closes with a useful next question.'),
('Farewell to Elder','C0','Elder Papa Mama PomPom PinPin Rabbit','Mentor leaves by named route, family knows his next location.'),
('Family path home','F0','Papa Mama PomPom PinPin Rabbit Scooby','Supported infant/carriers remain accounted for.'),
('Rabbit leaves with leaves','H0','Rabbit PinPin Papa','Exactly two boats go with Rabbit again; return plan explicit.'),
('Paw cloth routine','H0','Papa Scooby Mama PomPom','Wipe the moderate wet/soil paws before dog enters.'),
('Map beside supper','H1','Mama Papa PinPin PomPom','Discuss observed route and a question for tomorrow while infant remains supported.'),
('Quiet beds','H2','Mama Papa PinPin PomPom','Four-family rest closes day2; dog\'s cushion continuity is noted separately.')
],
[
('Day3 morning','H1','Mama Papa PinPin PomPom','Explicit fresh day with prior map on same safe shelf/table.'),
('Map question','H1','Papa PinPin','Recall branching stream; do not claim yesterday\'s clue solved everything.'),
('Mother checks small supplies','H1','Mama PomPom','Real care/packing with supported infant.'),
('Rabbit and leaves','H0','Rabbit PinPin Papa','Bring the same two damp-kept leaves for observation, not unintroduced props.'),
('Forest fork again','F0','Papa Mama PomPom PinPin Rabbit Scooby','Same entrance route and carriers; no new landscape teleport.'),
('Marker1 still there','C0','Papa PinPin Rabbit Scooby','Check established marker1 before entering.'),
('Sunlit family station','C1','Mama PomPom Papa','Explain mother/infant\'s broad station and scout-group route.'),
('PomPom watches reflection','C1','Mama PomPom','Meaningful supported sensory beat, not a dropped subplot.'),
('Return to echo pool','C3','Papa PinPin Rabbit Scooby','Recognisable chamber/light/stream geometry.'),
('Listen before guessing','C3','PinPin Rabbit Papa','Individual concentration/registers establish observation.'),
('Marker2 and fork','C4','Papa PinPin Rabbit','Orient from second strip and actual branches.'),
('First leaf test','C4','PinPin Rabbit Papa','Release leaf1 into chosen shallow flow with clear holder/state.'),
('Second leaf test','C4','PinPin Rabbit Papa','Release leaf2 to the other observed branch; no extra boat.'),
('Watch their directions','C4','PinPin Rabbit Papa','Follow actual flow, not an inconsistent uphill current.'),
('One slows','C4','PinPin Rabbit','An eddy produces a small problem/question; faces puzzled.'),
('Look around the root','C4','Papa PinPin Rabbit Scooby','Parent helps the view rather than supplying a final magic solution.'),
('Other leaf appears','C5','Papa PinPin Rabbit Scooby','Linked chamber reveals continuation; maintain boat counts/positions.'),
('Gather both leaves','C5','PinPin Rabbit Papa','Retrieve exactly both; resolve temporary ownership/split.'),
('Map amended','C5','Papa PinPin Rabbit','Only observed connections added to the single map.'),
('Scooby notices daylight','C5','Papa Scooby','Nose/ears identify outlet direction; useful dog role.'),
('Toward brighter roots','C6','Papa PinPin Rabbit Scooby','Show route to natural broad outlet, no stairs/cliff rescue.'),
('Outlet established','C6','Papa PinPin Rabbit Scooby','Wide daylight forest exit and stream direction.'),
('Third strip','C6','Papa PinPin Rabbit','Place marker3; exactly three strips total, locations stable.'),
('Return with the news','C1','Papa PinPin Rabbit Scooby Mama PomPom','Show return path to family station and explain next short route.'),
('Infant response','C1','Mama PomPom PinPin','Baby reaches for child\'s pointing paw while supported; quiet shared attention.'),
('Outside stream','S1','Papa Mama PomPom PinPin Rabbit Scooby','Move together to shown forest outlet stream.'),
('Beaver at stream','S1','Beaver Papa PinPin Rabbit','Established supporting character appears at his plausible outdoor place.'),
('Tell Beaver observations','S1','Beaver Papa PinPin Rabbit','Children explain what they saw, not a new engineering commission.'),
('Beaver\'s limited clue','S1','Beaver PinPin Rabbit Papa','One observation about a downstream route; no instant answer/map of unseen water.'),
('Follow the clue','S1','Papa Mama PomPom PinPin Rabbit Scooby','Observable broad path/current before inference.'),
('Lake glimpse','L0','Papa Mama PomPom PinPin Rabbit Scooby','Connect the outlet to established lake; no unsourced full explanation of former drying magic.'),
('Known ducks if shown','L0','PinPin Rabbit Papa','If visible, previous twelve: two adults/ten small; cropped view names visible subset honestly.'),
('Observation shared','L0','Papa PinPin Rabbit Mama PomPom','Water can travel where they did not see it; prior mystery receives a clue, not a false solved history.'),
('Birds and fallen drops','T0','BlueTit Robin Papa PinPin Rabbit Scooby','At chosen tree near root entrance, a few natural leaf drops inspire a question.'),
('Choose this tree','T0','Papa PinPin Rabbit Mama PomPom Scooby','Establish shower tree, safe dry-side place and exact overhead leaf.'),
('Known circle recalled','T0','PinPin Papa Rabbit','Child remembers the golden circle and reverse stop learned in previous chapter.'),
('Reach the chosen leaf','T0','Papa PinPin Scooby','Parent helps child reach deliberately; no spawned ladder or constructed steps.'),
('Small incomplete arc','T0','PinPin Papa','Trace small gold arc at chosen leaf/air point; no magic flow before completion.'),
('Circle closes','T0','PinPin Papa Rabbit Scooby','One completed source creates gentle falling water through canopy.'),
('Check falling flow','T0','Papa Mama PomPom PinPin','Parents check flow/pleasant temperature; infant stays supported on dry side.'),
('Watch where it goes','T0','Papa PinPin Rabbit','Observe runoff direction without a huge flood or invented aqueduct.'),
('Reverse starts','T0','PinPin Papa Rabbit','Use known reverse direction; competence, not relearning the entire old plot.'),
('Thin stream','T0','PinPin Papa Rabbit Scooby','Gold line fades and flow thins visibly.'),
('Last drop and quiet leaf','T0','Papa PinPin Rabbit Mama PomPom Scooby','Source is OFF before leaving. Only natural dew can remain.'),
('Beaver farewell','S1','Beaver Papa PinPin Rabbit','Supporting promise/location closes explicitly.'),
('Homeward route','F0','Papa Mama PomPom PinPin Rabbit Scooby','Map/leaves/markers and carriers accounted for.'),
('Rabbit\'s tomorrow promise','H0','Rabbit PinPin Papa','Agree to final visit/assisting roles; two leaves still go with Rabbit.'),
('Moderate paw cleanup','H0','Papa Scooby','Incidental soil removed visibly before indoor return.'),
('Show Mama gear idea','H1','Papa Mama PinPin PomPom','Name the shower gear for tomorrow so nothing materialises at the forest wash.'),
('Lay out actual gear','H1','Papa Mama PinPin PomPom','Two ochre towels, mat, small shampoo and brush ready beside bag; not a bathtub.'),
('Dry-side baby care','H1','Mama PomPom','Familiar mother/infant routine and clean infant cloth.'),
('Map put away','H1','Papa PinPin','One map and tomorrow\'s preparation have a definite place.'),
('Day3 sleep','H2','Mama Papa PinPin PomPom','Close with four-family rest; no unattended magic water anywhere.')
],
[
('Final-day light','H2','Mama Papa PinPin PomPom','Open day4 with clear morning/light state.'),
('Breakfast calmly','H1','Mama Papa PinPin PomPom','Familiar ordinary family beginning, varied acting not replayed identical grins.'),
('Check gear list','H1','Papa PinPin Mama PomPom','Recall visibly laid-out items from yesterday.'),
('Pack two towels','H1','Papa PinPin','Exactly T1/T2, dry and folded.'),
('Pack bottle and brush','H1','Papa PinPin','One small blue capped dog-shampoo bottle and one wooden-backed brush.'),
('Roll the mat','H1','Papa Rabbit PinPin','Rabbit has actually arrived for promised help; one mat added to the bag.'),
('Infant and family supplies','H1','Mama PomPom','Mother supports infant; normal food/flask/cups accounted for separately.'),
('Scooby waits at step','H0','Papa Scooby','Practice callback; clean coat at departure, not already mysteriously filthy.'),
('Leave together','F0','Papa Mama PomPom PinPin Rabbit Scooby','Assigned carriers and actual family journey.'),
('Forest landmark','F1','Papa Mama PomPom PinPin Rabbit Scooby','Recognise roots/birch from earlier days.'),
('Marker1 checked','C0','Papa PinPin Rabbit Scooby','Entrance and strip unchanged.'),
('Family at daylight lobby','C1','Mama PomPom Papa PinPin Rabbit Scooby','Supported infant/mother have a clear safe station, not disappearance.'),
('Warm berry gallery','C2','Papa PinPin Rabbit Scooby','Final purposeful look uses established chamber connections.'),
('Flower observation','C5','Papa PinPin Rabbit Scooby','New detail within established plants/light, not a new unrelated world.'),
('Dog catches damp scent','C5','Papa Scooby','Nose follows wet root/clay beside broad path.'),
('Clay on forepaws','C5','Papa Scooby PinPin Rabbit','First visible day4 dirt change, not a few later freckles.'),
('Body brushes wet roots','C5','Papa Scooby','Dirty lower chest/flank joins paws; physical cause shown.'),
('More vigorous scratch','F1','Papa Scooby PinPin Rabbit','At outdoor damp bank near exit, dig moves wet earth onto all legs/belly.'),
('A muddy roll','F1','Papa Scooby PinPin Rabbit','One joyful shoulder roll in same wet soil creates heavy opaque body dirt.'),
('Look at the result','F1','Papa PinPin Rabbit Scooby','Full body: all four legs/paws, belly/chest, flank and parts of back dirty. Others react differently.'),
('Wait really works','F1','Papa Scooby','Practiced cue stops another roll; not a trapped dog or rescue subplot.'),
('Mother sees the mud','C1','Mama PomPom Papa Scooby PinPin Rabbit','Raised brow/wry care with supported infant; heavy dirt does not reset.'),
('Toward chosen shower tree','T0','Papa Mama PomPom PinPin Rabbit Scooby','Shown route to already tested location, with actual bag/gear.'),
('Unroll carried mat','T0','Papa PinPin Rabbit Scooby','One mat on firm ground; keep soil/flowers/leaf source landmarks stable.'),
('Towels set aside','T0','PinPin Rabbit Papa','T1/T2 dry-side positions named; no infinite dry towels.'),
('Soap and brush ready','T0','Papa PinPin','Unpack actual capped bottle/brush; no new bath or jug from nowhere.'),
('Scooby doubtful','T0','Papa Scooby','Dog leans back slightly, mouth closed, eyes on canopy/parent; no generic smile.'),
('Mother/infant dry side','T0','Mama PomPom','Baby supported well outside shower; mother stays active and watchful.'),
('Circle traced deliberately','T0','PinPin Papa','One incomplete gold arc, no flow until closed.'),
('Falling canopy water','T0','PinPin Papa Rabbit Scooby','One closed source starts already tested gentle shower.'),
('Warm flow checked','T0','Papa Mama PomPom PinPin','Confirm pleasant gentle water; child remains attentive to live source.'),
('Nose tests droplets','T0','Papa Scooby','Dog sniffs one edge of falling water; face/eyes kept clear.'),
('One paw on mat','T0','Papa Scooby','Voluntary first step; other dirty paws/body do not become clean early.'),
('Body under shower','T0','Papa PinPin Scooby','All four paws supported; water wets the heavy mud before shampoo.'),
('Loosen wet soil','T0','Papa Scooby PinPin','Rinsing begins; visible brown runnels, not an instant golden coat.'),
('Small shampoo lather','T0','Papa PinPin Scooby','Use unpacked bottle; fixed cap state; gentle brush, no face/ear suds.'),
('Brush body','T0','Papa Scooby PinPin','Focused hands and first dog comfort; avoid frozen delighted human faces.'),
('One paw cleaned','T0','Papa Scooby PinPin','Lift one paw naturally while others support; wash toes/pads deliberately.'),
('Remaining paws','T0','Papa Scooby PinPin','Complete paw care with visible state change, not duplicate/impossible legs.'),
('Full final rinse','T0','Papa Scooby PinPin','All shampoo/dirt washed away; dog now clean but still wet. Papa rinses the brush bristles before setting it on the dry-side gear cloth.'),
('Reverse the circle','T0','PinPin Papa Rabbit','Known stop occurs while father supports the wash task.'),
('Last drop / source off','T0','PinPin Papa Mama PomPom Scooby Rabbit','Gold fades, last drop, quiet tree. No ongoing magic flow left behind.'),
('Step onto T1','T0','Papa Scooby PinPin','Clean wet dog steps onto first towel, not a magically dry coat.'),
('Still before shake','T0','Papa Scooby PinPin Rabbit','Body tension/ears warn; humans notice with actual expectancy/startle.'),
('Enormous shake','T0','Papa Scooby PinPin Rabbit','Water flies from four-legged grounded dog; mother/infant stay dry-side.'),
('Wet reactions','T0','Papa PinPin Rabbit Mama PomPom Scooby','Wry father, startled child, damp Rabbit ears; infant\'s brief earned response, not everyone grinning.'),
('T2 dries coat','T0','Papa Scooby PinPin','Second towel remains dry until now; T1 is already wet.'),
('Brush loose hair','T0','Papa Scooby PinPin','Canonical coat and modest shed hair; no huge new toy-dog fluff duplicate.'),
('Pack used gear','T0','Papa PinPin Rabbit Mama PomPom','Bottle cap replaced, brush/mat stored, wet/dry items distinguished.'),
('Farewell to forest helpers','F1','Papa PinPin Rabbit Mama PomPom Scooby','Return by C6→C5→C4→C1→C0, collecting marker3, marker2 then marker1; show the three strips in the bag at F1. Say farewell to the forest; sources off.'),
('Path home','F0','Papa Mama PomPom PinPin Rabbit Scooby','Clean/dry dog and bag leave by known route.'),
('Rabbit goes home','H0','Rabbit PinPin Papa Scooby','Actual farewell/payoff, future play promise sensible; no unclosed guest location.'),
('Correct full-body welcome','H0','Papa Scooby PinPin Mama PomPom','One green doorway, familiar room, whole dog/natural scale. He already belongs to the house.'),
('Family account and care','H1','Mama Papa PinPin PomPom Scooby','Share cave discovery and mother\'s daily care refrain; infant supported. Hang both used towels to dry and put the map on its shelf.'),
('Yawns and settling','H2','Mama Papa PinPin PomPom','Mama repeats the daily rest refrain; four family members settle into the familiar broad bed with supported PomPom.'),
('Home at rest','H1','Scooby','Clean dry Scooby sleeps on his established common-room cushion; the family is already settled in H2 and the forest source remains off.')
]
]
assert [len(x) for x in days]==[52,54,53,56],[len(x) for x in days]
scenes=[];number=0
for day,rows in enumerate(days,1):
 for title,location,cast,purpose in rows:
  number+=1
  # Actor directions are separate from identity. These are targets, not pixel-review claims.
  actors=[]
  for name in cast.split():
   if name=='Scooby':reg={'eyes':'on named scent/hand/path/water task, never default camera gaze','brows':'natural attentive; doubt/comfort/startle only when beat calls for it','mouth':'relaxed closed or natural pant, never copied toothy grin','ears':'respond to cue/sound/water and body state','posture':'named action with exactly four attached supporting/occluded legs'}
   elif name=='PomPom':reg={'eyes':'curious or naturally sleeping at night; distinct infant','brows':'soft curiosity, surprise or earned spoon/echo pleasure','mouth':'quiet, small sound or brief earned laugh; not pasted grin','posture':'supported by named adult/bedding; never standing/walking/submerged'}
   elif name in ['BlueTit','Robin']:reg={'eyes':'on current/leaf/nearby actor','mouth':'closed beak or small chirp when specified','posture':'one grounded/perched/flying bird body, same species/count'}
   else:reg={'eyes':'on the actual actor/object named in this beat','brows':'attentive, puzzled, firm, wry or surprised as consequence requires','mouth':'relaxed closed or small speaking opening; smile only for an earned beat','posture':'do the named task; hands/weight/body scale remain possible'}
   lower=(title+' '+purpose).lower()
   if any(w in lower for w in ['doubt','mud','wait','check','inspect','map','trace','test','listen','observe','puzzl','reverse','recognise','warm flow']):reg['register']='focused/curious/firm/wry; NO automatic grin'
   elif any(w in lower for w in ['sleep','bedtime','rests','rest','settling']):reg['register']='quiet/affectionate/drowsy where appropriate; natural closed eyes for sleep'
   elif any(w in lower for w in ['shake','wet reactions']):reg['register']='anticipation/startle/wry reaction, actor-specific'
   elif any(w in lower for w in ['spoon','echo','tiny','greeting','bread']):reg['register']='small earned pleasure or surprise for focal actor; others attentive'
   else:reg['register']='calm task-directed attention; individual reactions, no collective default smile'
   actors.append({'id':name,'actingTarget':reg})
  if day==1:soil='clean' if number<25 else 'light forepaw soil' if number<49 else 'paw cleaning / clean indoors'
  elif day in [2,3]:soil='clean at departure, incidental wet/soily paws on excursion, explicitly cleaned before home'
  else:
   local=number-159;soil='clean' if local<16 else 'new forepaw clay' if local==16 else 'increasing lower coat dirt' if local<19 else 'HEAVY opaque mud on all legs/paws, belly/chest/flank/back patches; persist until wash' if local<35 else 'progressively washed; no instant reset' if local<40 else 'clean wet' if local<47 else 'clean towel-dried and brushed'
  magic='absent / no new source' if day<3 else 'planned test only; explicit incomplete/closed/reverse/thin/last-drop/OFF sequence, never left running' if day==3 else 'OFF until deliberate start at local29–30; flowing through local40; reverse41; last-drop/OFF42; remainsOFF'
  if day==3:
   local=number-106;magic='OFF / absent' if local<38 else 'incomplete arc, NO flow' if local==38 else 'one closed source FLOWING' if local<42 else 'reverse begins' if local==42 else 'thinning' if local==43 else 'last drop then OFF' if local==44 else 'OFF'
  if day==4:
   local=number-159;magic='OFF' if local<29 else 'incomplete arc, NO flow' if local==29 else 'one closed source FLOWING' if local<41 else 'reverse begins' if local==41 else 'last drop then OFF' if local==42 else 'OFF'
  infant='Papa' if day==1 and number<=4 else 'Papa→Mama supported handover' if day==1 and number==5 else 'Mama or appropriate supported bedding at night'
  if day==2 and number==62:infant='Papa supports infant while Mama mounts lowered dog'
  if day==2 and number==63:infant='Papa→Mama supported return after mounting'
  if day==2 and number==67:infant='Mama→Papa before dismount; Papa→Mama on firm ground'
  if location=='H2':infant='supported shared bedding with parents'
  scenes.append({'id':f'r6-{number:03}','number':number,'day':day,'title':title,'location':location,'visibleCast':cast.split(),'purpose':purpose,'acting':actors,'continuityTargets':{'soil':soil,'magic':magic,'infantHolder':infant,'objects':'Follow CONTINUITY.md and OBJECTS.json; each image has exact before/after holder/count/state before generation','entranceExit':'Scene uses named map node; wider transitions precede changed locations'},'captionStatus':'English dialogue/EN-RU-ES pass follows beat/continuity lock; this is not final narration','artStatus':'not generated/selected','reviewStatus':'preproduction beat; requires full editorial and visible-art review'})
plan={'schemaVersion':1,'id':'scooby-cave-bath-r6','baseline':'Published Bath Magic R24,215 narrative scenes+title','status':'Complete215-beat preproduction structure; dialogue/three-language, precise object states and per-actor shot-specific acting pass still required before production batches','targetNarrativePages':215,'targetReaderPages':216,'languages':['en','ru','es'],'days':[{'day':d,'start':sum(len(x) for x in days[:d-1])+1,'end':sum(len(x) for x in days[:d])} for d in range(1,5)],'exclusions':['constructed stairs','deep-pit dog rescue','lost wooden boat subplot','unexplained forest bathtub','unattended magical water source','literal Minecraft block assets or game UI','uniform smiling faces'],'scenes':scenes}
(p/'BEAT-PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
(p/'BEATS.md').write_text('# R6 ordered beat plan\n\n215 scene purposes; captions/visual states are refined before art batches.\n\n'+'\n'.join(f"## Day{d}\n\n"+'\n'.join(f"- {s['id']} · **{s['title']}** ({s['location']}; {', '.join(s['visibleCast'])}): {s['purpose']}" for s in scenes if s['day']==d) for d in range(1,5))+'\n')
print('R6 beat counts:',[len(x) for x in days],'; total',len(scenes))
