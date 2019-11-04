class ShannonFano:

    def encode(self, tupleList, iA, iB):
        size = iB - iA + 1
        if size > 1:
            allSum = 0
            for i in range(iA, iB):
                allSum += tupleList[i][0]

            curSum = 0
            mid = -1
            #Calculate where the sum of top group is about equal with th sum of bottom group
            for i in range(iA, iB):
                curSum += tupleList[i][0]
                if curSum > allSum / 2:
                    mid = i
                    break;
            mid += 1

            for i in range(iA, iB + 1):
                tup = tupleList[i]
                if i < mid: #Top group
                    tupleList[i] = (tup[0], tup[1], tup[2] + '0')
                else: #Bottom group
                    tupleList[i] = (tup[0], tup[1], tup[2] + '1')
            #Do recursive calls for both groups
            self.encode(tupleList, iA, mid - 1 )
            self.encode(tupleList, mid, iB)
