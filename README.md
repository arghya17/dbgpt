```
V="europewest4.pkg.com/xyz-qqbc/eq-qw-wsd/pjl-eda:0.0.21"
V_UPDATED=$(echo "$V" | awk -F: '{split($NF, a, "."); a[length(a)]++; $NF=a[1]"."a[2]"."a[3]; print $0}' OFS=":")
echo "$V_UPDATED"
```
