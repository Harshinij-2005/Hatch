
B2C - Dangerous Patterns
Bug 1 :
   The validate() function itself tell the frappe, 
   like if once the datas are checked then automatically 
   the validate() function itself will save. So additional self.save()
    is not required here.
Bug 2 :
   Here every time if we update the booking value then the no.of.times 
   booked is updation and create chaos so that should be only done when
   we submit.  

Corrected Code:
  def validate(self):
    self.total_amount = sum(r.amount for r in self.addons) + self.base_amount

def on_submit(self):
    resource = frappe.get_doc("Resource", self.resource)
    resource.times_booked += 1
    resource.save()

B2d
 Say for example if there is two front-desk staffs named Staff A and 
 Staff B. If suppose Staff A edits the document and save it first and 
simultaneously Staff B modifies it it should display as "Document has
 been modified after you have opened it" as it compares the modified 
time with frappe db time and displays the msg instead of silently 
modifying the recent update

E1
   If self.save() is called inside on_update recurcive error will 
   happen because once on_update is called, it will automatically 
   call self.save(), which results in recursion, means the function
   calls itself causing a never ending loop.   

E2 — Naming & Renaming
   An utility function frappe.rename_doc() was used to rename 
```python
@frappe.whitelist()
def rename_member(old_name, new_name):
    frappe.rename_doc(
        "Member",
        old_name,
        new_name,
        merge=False
    )

If we use merge=true then pre existing records will link to current 
records and create confusion

H1 — Booking Form Script

The live availability check is triggered when the user changes the resource, booking date, start time, or end time.

This check should not be performed inside the client-side `validate` event by treating `frappe.call` as a synchronous operation.

`frappe.call` is asynchronous. The browser sends the request to the server and continues executing JavaScript. The server response becomes available later through the callback or Promise. Therefore, the response cannot be used immediately as if the server call had already completed.

The `validate` event is part of the save or submit process. Live availability is a UX preview that should be shown while the user is entering or changing booking details.

Therefore, the availability check is placed in field-change handlers for:

- `resource`
- `booking_date`
- `start_time`
- `end_time`

Whenever one of these values changes, the client calls the whitelisted server method `get_live_availability` and displays the current availability.

The live availability message is only a UX preview. It does not replace the server-side capacity validation because availability can change between the preview and the actual save or submit operation. The server-side validation remains the final authority.


Group I-Reports

F-string:-

```python
query = f"SELECT * FROM `tabBooking` WHERE booking_date >= '{today}'"
```
Parameterized:-
```python
query = "SELECT * FROM `tabBooking` WHERE booking_date >= %(today)s"
frappe.db.sql(query, {"today": today})
```
Parameterized queries are safer because values are passed separately from the SQL. They help prevent SQL injection and handle dynamic values properly.

