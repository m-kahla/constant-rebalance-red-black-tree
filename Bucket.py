class Item():
    def __init__(self, key, value, bucket):
        self.key = key
        self.value = value
        self.parent = None  # the item that preceds this item in the bucket(list)
        self.child = None  # the item that follows this item in the bucket
        self.current_bucket = bucket


class Bucket():
    def __init__(self, left_bucket, right_bucket, parent_node):
        self.left_bucket = left_bucket
        self.right_bucket = right_bucket

        self.start = None  # first item
        self.middle = None  # middle item
        self.end = None  # last item

        self.count = 0  # count of items in the bucket
        self.smaller_count = 0  # count of items that are smaller than the middle
        self.larger_count = 0  # count of items that are larger than the middle

        self.outdated = False
        self.newer_bucket = None  # in case bucket has been merged and became outdated.... this is the new bucket
        self.newer_left_bucket = None  # in case bucket has been split and became outdated.... this is the new left bucket
        self.newer_right_bucket = None

        self.fixing_pointer = None
        self.inside_fixing_pointer = None  # this is resnposible for making sure incrementally that each item points to its current bucket

        self.parent_node = parent_node

    def insert_item(self, key, value):
        new_item = Item(key, value, self)
        if self.count == 0:
            self.start = new_item
            self.middle = new_item
            self.end = new_item
            self.inside_fixing_pointer = self.start
        else:
            temp_item = self.start
            while temp_item != None:
                if key >= temp_item.key:
                    if temp_item == self.end:
                        self.end.child = new_item
                        new_item.parent = self.end
                        self.end = new_item
                        self.larger_count += 1
                        break
                    else:
                        temp_item = temp_item.child

                else:
                    if temp_item is not self.start:
                        temp_item.parent.child = new_item
                        new_item.parent = temp_item.parent
                    else:
                        self.start=new_item
                    new_item.child = temp_item
                    temp_item.parent = new_item
                    if key >= self.middle.key:
                        self.larger_count += 1
                    else:
                        self.smaller_count += 1
                    break
        self.count += 1




    def delete_item(self,key):  # if there are multiple items with the same key, we delete the first occurence of this key
        temp_item = self.start
        while temp_item != None:
            if key == temp_item.key:
                if temp_item.parent != None:
                    temp_item.parent.child = temp_item.child
                if temp_item.child != None:
                    temp_item.child.parent = temp_item.parent
                self.count -= 1
                if self.count == 0:
                    self.start = None
                    return
                if temp_item == self.start:
                    self.start = self.start.child
                if temp_item == self.middle:
                    if self.middle.child != None:
                        self.middle = self.middle.child
                        self.larger_count -= 1
                    elif self.middle.parent != None:
                        self.middle = self.middle.parent
                        self.smaller_count -= 1  # it is impossible to be neither of those cases because this will mean that there was only this item in the bucket and that case was already handled above
                else:
                    if temp_item.key<self.middle.key:
                        self.smaller_count-=1
                    else:
                        self.larger_count-=1
                if temp_item == self.end:
                    self.end = self.end.parent
                if temp_item == self.inside_fixing_pointer:
                    if self.count > 0 and self.inside_fixing_pointer.child != None:
                        self.inside_fixing_pointer = self.inside_fixing_pointer.child
                    elif self.count > 0 and self.inside_fixing_pointer.parent != None:
                        self.inside_fixing_pointer = self.inside_fixing_pointer.parent
                    else:  # this means count is 0
                        self.inside_fixing_pointer = None
                break
            else:
                if key < temp_item.key:
                    return
                else:
                    temp_item = temp_item.child

    def split(self):  # dont forget to check if global pointer points to split or merged bucket
        self.outdated = True
        self.finish_post_operations()
        new_left = Bucket(self.left_bucket, None, None)
        new_right = Bucket(None, self.right_bucket, None)
        new_left.right_bucket = new_right
        new_right.left_bucket = new_left
        if self.left_bucket != None:
            self.left_bucket.right_bucket = new_left
        if self.right_bucket != None:
            self.right_bucket.left_bucket = new_right

        new_left.start = self.start
        new_left.middle = self.start  # middle pointer after splitting will point to the start node and will be corrected before splitting again
        new_left.end = self.middle.parent
        new_left.end.child = None
        new_left.count = self.smaller_count
        new_left.smaller_count = 0
        new_left.larger_count = new_left.count - 1
        new_left.inside_fixing_pointer = new_left.start

        new_right.start = self.middle
        new_right.start.parent = None
        new_right.middle = new_right.start
        new_right.end = self.end
        new_right.count = self.larger_count + 1
        new_right.smaller_count = 0
        new_right.larger_count = new_right.count - 1
        new_right.inside_fixing_pointer = new_right.start


        return new_left, new_right, self.middle.key, self.middle.value

    def merge(self, right_merged_bucket):
        left_merged_bucket = self
        self.finish_post_operations()
        new_merged = Bucket(left_merged_bucket.left_bucket, right_merged_bucket.right_bucket, None)
        if left_merged_bucket.left_bucket != None:
            left_merged_bucket.left_bucket.right_bucket = new_merged
        if right_merged_bucket.right_bucket != None:
            right_merged_bucket.right_bucket.left_bucket = new_merged

        # mark both buckets as outdated and make them point to the new merged bucket
        left_merged_bucket.outdated = True
        left_merged_bucket.newer_bucket = new_merged
        right_merged_bucket.outdated = True
        right_merged_bucket.newer_bucket = new_merged

        # adjust start,middle,end items for the new bucket
        new_merged.start = left_merged_bucket.start
        new_merged.middle = right_merged_bucket.start
        new_merged.middle.parent = left_merged_bucket.end
        new_merged.middle.parent.child = new_merged.middle
        new_merged.end = right_merged_bucket.end

        new_merged.count = left_merged_bucket.count + right_merged_bucket.count
        new_merged.smaller_count = left_merged_bucket.count
        new_merged.larger_count = right_merged_bucket.count - 1

        new_merged.inside_fixing_pointer = new_merged.start
        left_merged_bucket.start=left_merged_bucket.middle=left_merged_bucket.end=None
        right_merged_bucket.start=right_merged_bucket.middle=right_merged_bucket.end=None
        left_merged_bucket.count=left_merged_bucket.larger_count=left_merged_bucket.smaller_count=0
        right_merged_bucket.count=right_merged_bucket.smaller_count=right_merged_bucket.larger_count=0
        return new_merged

    def borrow(self, other_bucket):
        if other_bucket == self.right_bucket:
            # add the right bucket's first element to the end of the left bucket and mark the second element in the right bucket as the start
            temp_item = other_bucket.start
            other_bucket.start = other_bucket.start.child
            other_bucket.start.parent = None
            if self.count == 0:
                self.start=temp_item
                self.start.parent=None
                self.start.child=None
                self.middle=self.start
                self.end =self.start
                self.inside_fixing_pointer=self.start
            else:
                self.end.child = temp_item
                self.end.child.parent = self.end
                self.end = self.end.child
                self.end.child = None
                self.end.current_bucket = self
                self.larger_count += 1

            if other_bucket.middle == self.end:
                other_bucket.middle = other_bucket.start
                other_bucket.larger_count -= 1
            else:
                other_bucket.smaller_count -= 1
            key = self.end.key
            value = self.end.value
        elif other_bucket == self.left_bucket:
            # add left bucket's last element to the begining of the right bucket
            temp_item = other_bucket.end
            other_bucket.end = other_bucket.end.parent
            other_bucket.end.child = None
            if self.count == 0:
                self.start=temp_item
                self.middle=self.start
                self.end =self.start
                self.inside_fixing_pointer=self.start
            else:
                self.start.parent=temp_item
                self.start.parent.child = self.start
                self.start = self.start.parent
                self.start.parent = None
                self.start.current_bucket = self
                self.smaller_count += 1

            if other_bucket.middle == self.start:
                other_bucket.middle = other_bucket.end
                other_bucket.smaller_count -= 1
            else:
                other_bucket.larger_count -= 1

            key = self.start.key
            value = self.start.value

        
        other_bucket.count -= 1
        self.count += 1

        return key, value

    def post_operation(self):
        if self.smaller_count - self.larger_count >= 2:
            self.middle = self.middle.parent
            self.larger_count += 1
            self.smaller_count -= 1
        elif self.larger_count - self.smaller_count >= 2:
            self.middle = self.middle.child
            self.smaller_count += 1
            self.larger_count -= 1
        if self.inside_fixing_pointer != None:
            self.inside_fixing_pointer.current_bucket = self
            self.inside_fixing_pointer = self.inside_fixing_pointer.child

    def finish_post_operations(self):  # it is proved that this will be constant once the bucket is ready to be split or merged
        while abs(self.smaller_count - self.larger_count) > 1:
            if self.smaller_count > self.larger_count:
                self.middle = self.middle.parent
                self.larger_count += 1
                self.smaller_count -= 1
            else:
                self.middle = self.middle.child
                self.smaller_count += 1
                self.larger_count -= 1
        while self.inside_fixing_pointer != None:
            self.inside_fixing_pointer.current_bucket = self
            self.inside_fixing_pointer = self.inside_fixing_pointer.child
