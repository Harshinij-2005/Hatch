
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
