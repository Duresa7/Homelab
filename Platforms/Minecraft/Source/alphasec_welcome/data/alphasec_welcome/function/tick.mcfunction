execute as @a unless score @s asu.wlc.session = #current asu.wlc.session run function alphasec_welcome:welcome
execute as @a[scores={asu.wlc.leave=1..}] run function alphasec_welcome:welcome
