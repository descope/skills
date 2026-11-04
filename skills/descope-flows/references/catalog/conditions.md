# Condition operators

Generated from Descope's action definitions. Do not edit by hand.

Use the id as `operator` in a condition task's `atomicConditions`. `Target only` operators take no predicate. `Applies to` is the target's type.

| Operator | Name | Applies to | Target only | Description |
|---|---|---|---|---|
| `contains` | Contains | string |  | Determine if the target contains the predicate, supports both lists and strings |
| `divided-by` | Divided By | number, abtesting |  | Determine if value is divided by predicate |
| `doesnt-contains` | Doesn't Contain | string |  | Determine if the target doesn't contain the predicate, supports both lists and strings |
| `empty` | Is Empty | string, ipaddress | yes | Determine value is empty |
| `equal` | Equals | string, number, ipaddress |  | Determine if two values are equivalent |
| `greater-than` | Greater Than | number, abtesting |  | Determine the target is greater than its predicate |
| `greater-than-or-equal` | Greater Than or Equal | number, abtesting |  | Determine the target is greater than or equal to its predicate |
| `in` | In | string |  | Determine if value is in the array |
| `in-range` | In Range | number, abtesting |  | Determine if value is in range |
| `ip-address-in` | IP Address In | string, ipaddress |  | Determine if an IP address is within a list of ranges |
| `is-approved-domain` | Is Approved Domain | string | yes | Validate if domain is the approved domain list |
| `is-email` | Is Email | string | yes | Determine value is a valid email address |
| `is-false` | Is False | boolean | yes | Determine value is false |
| `is-phone` | Is Phone | string | yes | Determine value is a valid phone number |
| `is-true` | Is True | boolean | yes | Determine value is true |
| `less-than` | Less Than | number, abtesting |  | Determine the target is less than its predicate |
| `less-than-or-equal` | Less Than or Equal | number, abtesting |  | Determine the target is less than or equal to its predicate |
| `lists-contains` | Lists Contains | list |  | Determine if the list contains the target |
| `lists-not-contains` | Lists Not Contains | list |  | Determine if the list does not contain the target |
| `matches` | Matches | string |  | Determine if the target matches the regex predicate, supports strings |
| `newer-days` | Over x days ago | time |  | Determine if value is over x days from now |
| `newer-hours` | Over x hours ago | time |  | Determine if value is over x hours from now |
| `newer-minutes` | Over x minutes ago | time |  | Determine if value is over x minutes from now |
| `not-empty` | Is Not Empty | string, ipaddress | yes | Determine value is not empty |
| `not-equal` | Doesn't Equal | string, number, ipaddress |  | Determine if two values are not equivalent |
| `not-in` | Not In | string |  | Determine if value is not in the array |
| `not-in-range` | Not In Range | number, abtesting |  | Determine if value is not in range |
| `older-days` | Within x days ago | time |  | Determine if value is within x days from now |
| `older-hours` | Within x hours ago | time |  | Determine if value is within x hours from now |
| `older-minutes` | Within x minutes ago | time |  | Determine if value is within x minutes ago from now |
