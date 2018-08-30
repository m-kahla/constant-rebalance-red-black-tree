from Bucket import Bucket
from math import ceil,log
class Node:
	def __init__(self,key,value):
		self.key=key
		self.value=value
		self.doubly_black=False
		self.is_red=True #if false, therefore it is balck
		self.parent=None
		self.left=None
		self.right=None
		self.is_root=False
		self.has_bucket=False # if the node is a leaf then this attribute is True
		self.bucket=None 


class Tree:
	def __init__(self):
		self.root=None
		self.count=0
		self.count_for_next_H=4
		self.count_for_prev_H=-1
		self.global_bucket=None
		self.leftmost_bucket=None
		self.nil=Node(-1,-1)
		self.H=4.32 #current H of the tree
		self.bucket_list=[]



	def insert(self,key,value):
		if self.root==None:
			new_node=Node(key,value)
			new_node.is_red=False
			self.root=new_node
			self.count+=1

			left_child=Node(-1,-1) # this is an empty bucket
			left_child.is_red=False
			self.root.left=left_child
			left_child.parent=self.root
			left_child.has_bucket=True
			left_child.bucket=Bucket(None,None,left_child)
			left_child.bucket.fixing_pointer=self.nil
			self.leftmost_bucket=left_child.bucket

			right_child=Node(-1,-1)
			right_child.is_red=False
			self.root.right=right_child
			right_child.parent=self.root
			right_child.has_bucket=True
			right_child.bucket=Bucket(left_child.bucket,None,right_child)
			right_child.bucket.fixing_pointer=self.nil
			left_child.bucket.right_bucket=right_child.bucket

			self.global_bucket=self.leftmost_bucket

		else:
			#binary search till we find the bucket
			temp_node=self.root
			while temp_node.has_bucket==False:
				if key>=temp_node.key:
					temp_node=temp_node.right
				else:
					temp_node=temp_node.left
			bucket=temp_node.bucket
			#print("P0")		
			bucket.insert_item(key,value)
			#print("P1")		
			self.fixup(bucket)
			self.fixup(bucket)
			
			#check for splitting case

			if bucket.count>(2*self.H)-10 and bucket.count>20:
				self.split(temp_node)	
				
		#print("global_bucket.fixin pointer from insert is : ",self.global_bucket.fixing_pointer==self.nil)		
		#print("P2")		
		self.post_operation()
		self.update_H()
				
		return


	def delete(self,key):
		temp_node=self.root
		while temp_node.has_bucket==False:
			if key>=temp_node.key:
				temp_node=temp_node.right
			else:
				temp_node=temp_node.left
		bucket=temp_node.bucket
		bucket.delete_item(key)
		self.fixup(bucket)
		self.fixup(bucket)
		if bucket.count < (0.5*self.H) +3 and temp_node.parent != self.root :
			self.merge_or_borrow(temp_node)
				
		self.post_operation()
		self.update_H()
			
		

	def split(self,temp_node):
		bucket=temp_node.bucket	
		self.finish_remaining_fixups(bucket)
		new_left_bucket,new_right_bucket,key,value=bucket.split()
		#add the middle node of the bucket to the tree
		self.count+=1
		new_node=Node(key,value)
		new_node.parent=temp_node.parent
		if temp_node==temp_node.parent.left:
			temp_node.parent.left=new_node
		else:
			temp_node.parent.right=new_node
		#create the leaf nodes that contain the new split buckets
		left_leaf=Node(-1,-1) 
		left_leaf.is_red=False
		left_leaf.has_bucket=True
		left_leaf.bucket=new_left_bucket
		left_leaf.parent=new_node
		left_leaf.bucket.fixing_pointer=left_leaf.parent
		new_left_bucket.parent_node=left_leaf
		new_node.left=left_leaf

		right_leaf=Node(-1,-1)
		right_leaf.is_red=False
		right_leaf.has_bucket=True
		right_leaf.bucket=new_right_bucket
		right_leaf.parent=new_node
		right_leaf.bucket.fixing_pointer=right_leaf.parent
		new_right_bucket.parent_node=right_leaf
		new_node.right=right_leaf
		
		self.fixup(left_leaf.bucket) #as in paper we call fixup for one of the buckets to eliminate consequtive reds above any bucket
		self.fixup(left_leaf.bucket)
		if bucket==self.global_bucket:
			self.global_bucket=new_left_bucket
		if bucket==self.leftmost_bucket:
			self.leftmost_bucket=new_left_bucket


	def merge_or_borrow(self,temp_node):

		###### debug #######
		new_merged_bucket=None # yes this is in debug only
		self.bucket_list=[]
		self.dfs(self.root)
		prev_b=None
		index=0
		for b in self.bucket_list:
			index+=1
			if b.left_bucket !=prev_b:
				raise Exception("ERROR! bucket not pointing to its left after dfs in start of merge or borrow ",index,len(self.bucket_list))
			if prev_b!=None:
				if prev_b.right_bucket!=b:
					raise Exception("ERROR! bucket not pointing to its right bucket after dfs in start of merge or borrow   ",index,len(self.bucket_list))
			prev_b=b
		if b.right_bucket!=None:
			raise Exception("ERROR! rightmost doesnt point to None after dfs in start of merge or borrow ",len(self.bucket_list))
		###### debug ######

		bucket=temp_node.bucket
		self.finish_remaining_fixups(bucket)
		other_bucket=self.prepare_for_merge(temp_node)
		print(other_bucket==bucket.parent_node.parent.right.bucket)
		'''if other_bucket.count<=5:#we merge or borrow if both buckets have size greater than a certain constant ( thats our base case)
			print('return from merge or borrow')
			return'''
		if other_bucket.count > (0.5*self.H) +3:
			new_key,new_value=bucket.borrow(other_bucket)
			temp_node.parent.key=new_key
			temp_node.parent.value=new_value
			self.fixup(other_bucket)
			self.fixup(other_bucket)
		else:
			self.finish_remaining_fixups(other_bucket)
			'''other_bucket=self.prepare_for_merge(temp_node)
			self.finish_remaining_fixups(other_bucket)'''
			print(self.print_index(bucket),self.print_index(other_bucket))
			print(other_bucket==bucket.parent_node.parent.right.bucket)
			# create a new leaf that will point to the new merged bucket
			self.count-=1
			new_leaf=Node(-1,-1)
			new_leaf.is_red=False
			new_leaf.has_bucket=True
			if temp_node.parent.is_red==False: # if the removed parent was black then new bucket is doubly black
				new_leaf.doubly_black=True
			new_leaf.parent=temp_node.parent.parent
			# remove the merged buckets' parent
			if temp_node.parent==temp_node.parent.parent.left:
				temp_node.parent.parent.left=new_leaf
			elif temp_node.parent==temp_node.parent.parent.right:
				temp_node.parent.parent.right=new_leaf
			else:
				raise Exception("ERROR! parent and child nodes not pointing to each other ")

			print(self.print_index(bucket),self.print_index(other_bucket))
			if other_bucket== bucket.right_bucket: # we merge the right bucket into the left one
				print(other_bucket==bucket.parent_node.parent.right.bucket)
				new_merged_bucket=bucket.merge(other_bucket)
				print('bucket is left',bucket.left_bucket.right_bucket==new_merged_bucket,new_merged_bucket.left_bucket==bucket.left_bucket, other_bucket.right_bucket.left_bucket==new_merged_bucket,new_merged_bucket.right_bucket==other_bucket.right_bucket)
				if new_merged_bucket.left_bucket!= bucket.left_bucket or new_merged_bucket.right_bucket!= other_bucket.right_bucket:
					print("ERROR!! in new merged bucket")
					exit()
			elif other_bucket==bucket.left_bucket:
				print(other_bucket==bucket.parent_node.parent.left.bucket)
				new_merged_bucket=other_bucket.merge(bucket)
				print('bucket is right',bucket.right_bucket.left_bucket==new_merged_bucket,new_merged_bucket.right_bucket==bucket.right_bucket, new_merged_bucket.left_bucket== other_bucket.left_bucket , other_bucket.left_bucket.right_bucket==new_merged_bucket)
				if new_merged_bucket.left_bucket!= other_bucket.left_bucket or new_merged_bucket.right_bucket!= bucket.right_bucket:
					print("ERROR!! in new merged bucket")
					exit()
			else:
				print("ERROR!! buckets should be siblings")
				exit()


			new_merged_bucket.parent_node=new_leaf
			new_leaf.bucket=new_merged_bucket
			new_leaf.bucket.fixing_pointer=new_leaf
			new_bucket=new_leaf.bucket
			self.fixup(new_bucket)
			self.fixup(new_bucket)
			if bucket==self.global_bucket or other_bucket==self.global_bucket:
				self.global_bucket=new_merged_bucket
		if bucket==self.leftmost_bucket or other_bucket==self.leftmost_bucket:
			self.leftmost_bucket=new_merged_bucket
		###### debug #######
		self.bucket_list=[]
		self.dfs(self.root)
		'''print(self.print_index(new_merged_bucket))

		index=1
		for b0 in self.bucket_list:
			if b0 in self.bucket_list[index:]:
				raise Exception("ERROR! bucket is duplicated")
			if b0==new_merged_bucket:
				break
			index+=1
		print( ' merged bucket at index : ',index)'''

		prev_b=None
		index=0
		for b in self.bucket_list:
			index+=1
			if b.left_bucket !=prev_b:
				raise Exception("ERROR! bucket not pointing to its left after dfs in end of merge or borrow ",index,len(self.bucket_list))
			if prev_b!=None:
				if prev_b.right_bucket!=b:
					raise Exception("ERROR! bucket not pointing to its right bucket after dfs in end of merge or borrow   ",index,len(self.bucket_list))
			prev_b=b
		if b.right_bucket!=None:
			raise Exception("ERROR! rightmost doesnt point to None after dfs in end of merge or borrow ",len(self.bucket_list))
		###### debug ######

	def fixup(self,bucket):
		#print("global_bucket.fixin pointer from fixup is : ",self.global_bucket.fixing_pointer==self.nil)		
		if bucket.fixing_pointer!=self.root and bucket.fixing_pointer != self.nil :
			if bucket.fixing_pointer.is_red==True and bucket.fixing_pointer.parent.is_red==True:
				self.double_red_fixup(bucket.fixing_pointer)
			if bucket.fixing_pointer.doubly_black==True:
				self.doubly_black_fixup(bucket.fixing_pointer)


		#advance the fixing pointer to its parent
		if bucket.fixing_pointer==self.root or bucket.fixing_pointer.parent==self.root or bucket.fixing_pointer==self.nil:
			bucket.fixing_pointer=self.nil
		else:
			bucket.fixing_pointer=bucket.fixing_pointer.parent
		#bucket.print_bucket()
		bucket.post_operation()
		#bucket.print_bucket()
		return


	def finish_remaining_fixups(self,bucket): # this is proved in paper to be constant	
		while bucket.fixing_pointer != self.root and bucket.fixing_pointer != self.nil:
			self.fixup(bucket)
		return
		
			
	def prepare_for_merge(self,leaf_node): # this method ensures that the bucket's sibiling is a bucket not a node in constant time
		if leaf_node.parent.left==leaf_node: #		
			if leaf_node.parent.right.has_bucket==False:
				self.left_rotate(leaf_node.parent)
				print('rotation happened in prepare for merge')
			sibling_bucket=leaf_node.parent.right.bucket
			if leaf_node.parent.right.has_bucket==False:
				print("ERROR!! bucket sibling must be a bucket in prepare for merge")
				exit()
			if leaf_node.parent.right.bucket!=leaf_node.bucket.right_bucket:
				raise Exception("ERROR! in bucket pointers",leaf_node.parent.right.bucket==leaf_node.bucket.right_bucket, leaf_node.parent.right.bucket.left_bucket==leaf_node.bucket)
		else:
			if leaf_node.parent.left.has_bucket==False:
				self.right_rotate(leaf_node.parent)
				print('rotation happened in prepare for merge')
			sibling_bucket=leaf_node.parent.left.bucket
			if leaf_node.parent.left.has_bucket==False:
				print("ERROR!! bucket sibling must be a bucket in prepare for merge")
				exit()
			if leaf_node.parent.left.bucket!=leaf_node.bucket.left_bucket:
				raise Exception("ERROR! in bucket pointers",leaf_node.parent.left.bucket==leaf_node.bucket.left_bucket, leaf_node.parent.left.bucket.right_bucket==leaf_node.bucket)
			
		return sibling_bucket



	def left_rotate(self,node):
		if node != self.root:
			if node==node.parent.left:
				node.parent.left=node.right
			else:
				node.parent.right=node.right
			node.right.parent=node.parent
		else:
			self.root=node.right
		node.parent=node.right
		node.right=node.right.left
		node.right.parent=node
		node.parent.left=node
		return


	def right_rotate(self,node):
		if node != self.root:
			if node==node.parent.left:
				node.parent.left=node.left
			else:
				node.parent.right=node.left
			node.left.parent=node.parent
		else:
			self.root=node.left

		node.parent=node.left
		node.left=node.left.right
		node.left.parent=node
		node.parent.right=node


	def double_red_fixup(self,node): # takes a red node that has a red parent and perform a fixup
		if node.parent==node.parent.parent.left:
			uncle=node.parent.parent.right
			if uncle.is_red==True: # this is doubly red fixup case 1
				node.parent.is_red=False
				uncle.is_red=False
				if node.parent.parent.doubly_black==True:
					node.parent.parent.doubly_black=False # case 1.1
				else:
					node.parent.parent.is_red=True
			else:
				if node==node.parent.right: #case 2
					node=node.parent
					self.left_rotate(node)
				#case 3
				node.parent.is_red=False
				node.parent.parent.is_red=True
				if node.parent.parent.doubly_black==True:# case 3.1
					node.parent.parent.doubly_black=False
					node.parent.doubly_black=True
				self.right_rotate(node.parent.parent)
		else:
			uncle=node.parent.parent.left
			if uncle.is_red==True: # this is doubly red fixup case 1
				node.parent.is_red=False
				uncle.is_red=False
				if node.parent.parent.doubly_black==True:
					node.parent.parent.doubly_black=False # case 1.1
				else:
					node.parent.parent.is_red=True
			else:
				if node==node.parent.left: #case 2
					node=node.parent
					self.right_rotate(node)
				#case 3
				node.parent.is_red=False
				node.parent.parent.is_red=True
				if node.parent.parent.doubly_black==True:# case 3.1
					node.parent.parent.doubly_black=False
					node.parent.doubly_black=True
				self.left_rotate(node.parent.parent)
		self.root.is_red=False



	def doubly_black_fixup(self,node):
		if node==node.parent.left:
			s=node.parent.right
			if s.is_red==True:#case 1
				if node.parent.is_red==True:#case 1.1
					s.is_red=False
				node.parent.is_red=True
				self.left_rotate(node.parent)
				s=node.parent.right
			if s.is_red==True:#case 1 repeated since we allow two consecutive reds
				if node.parent.is_red==True:#case 1.1
					s.is_red=False
				node.parent.is_red=True
				self.left_rotate(node.parent)
				s=node.parent.right
			if s.doubly_black==True:#case 1.2
				node.doubly_black=False
				s.doubly_balck=False
				if node.parent.is_red==True:
					node.parent.is_red=False
				else:
					node.parent.doubly_black=True
				self.root.doubly_black=False
				return
			if s.left.is_red==False and s.right.is_red==False: #case2
				s.is_red=True
				node.doubly_black=False
				node.parent.doubly_black=True
				self.root.doubly_black=False
				return
			elif s.right.is_red==False:#case 3
				s.is_red=True
				s.left.is_red=False
				self.right_rotate(s)
			if s.right.is_red==True:# case 4
				s.is_red=node.parent.is_red
				node.parent.is_red=False
				s.right.is_red=False
				self.left_rotate(node.parent)

		else:
			s=node.parent.left
			if s.is_red==True:#case 1
				if node.parent.is_red==True:#case 1.1
					s.is_red=False
				node.parent.is_red=True
				self.right_rotate(node.parent)
				s=node.parent.left
			if s.is_red==True:#case 1 repeated since we allow two consecutive reds
				if node.parent.is_red==True:#case 1.1
					s.is_red=False
				node.parent.is_red=True
				self.right_rotate(node.parent)
				s=node.parent.left
			if s.doubly_black==True:#case 1.2
				node.doubly_black=False
				s.doubly_balck=False
				if node.parent.is_red==True:
					node.parent.is_red=False
				else:
					node.parent.doubly_black=True
				self.root.doubly_black=False
				return
			if s.left.is_red==False and s.right.is_red==False: #case2
				s.is_red=True
				node.doubly_black=False
				node.parent.doubly_black=True
				self.root.doubly_black=False
				return
			elif s.left.is_red==False:#case 3
				s.is_red=True
				s.right.is_red=False
				self.left_rotate(s)
			if s.left.is_red==True:# case 4
				s.is_red=node.parent.is_red
				node.doubly_black=False
				node.parent.is_red=False
				s.left.is_red=False
				self.right_rotate(node.parent)
				

				
		self.root.doubly_black=False
	

	def post_operation(self):
		

	
		#print("global_bucket.fixin pointer from post_operation is : ",self.global_bucket.fixing_pointer==self.nil)		
		bucket=self.global_bucket
		parent_node=bucket.parent_node
		if bucket.count>(2*self.H)-10 and bucket.count>20:
			self.split(parent_node)
		elif bucket.count < (0.5*self.H) +3 and parent_node.parent != self.root :
			print('start global merge')
			self.merge_or_borrow(parent_node)
			print('end global merge')
		else:
			for i in range(11):
				self.fixup(bucket)
			if bucket.right_bucket==None:
				self.global_bucket=self.leftmost_bucket
			else:
				self.global_bucket=bucket.right_bucket
		###### debug #######
		self.bucket_list=[]
		self.dfs(self.root)
		prev_b=None
		index=0
		for b in self.bucket_list:
			index+=1
			if b.left_bucket !=prev_b:
				raise Exception("ERROR! bucket not pointing to its left after dfs  ",index,len(self.bucket_list))
			if prev_b!=None:
				if prev_b.right_bucket!=b:
					raise Exception("ERROR! bucket not pointing to its right bucket after dfs  ",index,len(self.bucket_list))
			prev_b=b
		if b.right_bucket!=None:
			raise Exception("ERROR! rightmost doesnt point to None after dfs",len(self.bucket_list))
		###### debug ######
			
		return
	
	
	def update_H(self):
		if self.count>=self.count_for_next_H:
			self.count_for_prev_H=self.count_for_next_H
			self.count_for_next_H*=2
			self.H=ceil(4.32*log(self.count,2))
		elif self.count>=self.count_for_prev_H:
			self.count_for_next_H=self.count_for_prev_H	
			self.count_for_prev_H/=2
			self.H=ceil(4.32*log(self.count,2))
		return	
		

	def dfs(self,node):
		if node.has_bucket==True:
			self.bucket_list.append(node.bucket)
		else:
			self.dfs(node.left)
			self.dfs(node.right)


	
	def print_index(self,bucket):
		self.bucket_list=[]
		self.dfs(self.root)
		index=1
		for elem in self.bucket_list:
			if bucket==elem:
				return index
			index+=1
		return -1

	
	def print_tree():
		return
		
#####################   TEST   #################################
'''b1=Bucket(None,None,None)
b1.insert_item(0,0)
b1.insert_item(1,0)
b1.insert_item(2,0)
b1.print_bucket()
b2=Bucket(b1,None,None)
b1.right_bucket=b2
b2.insert_item(3,0)
b2.print_bucket()
b2.borrow(b1)
b1.print_bucket()
b2.print_bucket()'''


'''def print_bucket(b):
	temp_item=b.start
	while temp_item != None:
		s=''
		if temp_item==b.start:
			s+=' (S) '
		if temp_item==b.middle:
			s+=' (M) '
		if temp_item==b.end:
			s+=' (E) '
		print(temp_item.key, s)
		temp_item=temp_item.child


b=Bucket(None,None,None)
b.insert_item(0,0)
b.insert_item(1,0)
b.insert_item(2,0)
print_bucket(b)'''



#try:
t=Tree()
for i in range(1000):
	print(i)
	t.insert(i,i)
for i in range(1000):
	print(i)
	t.delete(i)	
#except Exception as e:
	#print (e)
'''

reminders:
merge only when each bucket has atleast 1 node
check invariant all leaves are buckets

'''
