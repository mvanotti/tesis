
class Block:
    def __init__(self, metric):
        self.hash = metric["hash"]
        self.parent_hash = metric["parent"]
        self.timestamp = metric["timestamp"]
        self.number = metric["number"]
        self.miner = metric["nodeID"]
        self.difficulty = 1 # TODO(mvanotti): Add this metric.

def get_key(block):
    return block.hash, block.number
def get_parent_key(block):
    return block.parent_hash, block.number - 1

class Blockchain:
    def __init__(self, genesis):
        self.genesis = genesis
        self.store = {}
        self.blocks_by_number = {0: genesis}
        self.difficulty = genesis.difficulty
        self.blocks_by_hash = { get_key(genesis): genesis}
        self.cumulative_difficulty = { get_key(genesis): genesis.difficulty}
        self.best_block = genesis
        self.max_block_num = 0

    def add_block(self, block):
        self.blocks_by_hash[get_key(block)] = block
        self.max_block_num = max(block.number, self.max_block_num)

        if block.number not in self.blocks_by_number:
            self.blocks_by_number[block.number] = set()
        self.blocks_by_number[block.number].add(block)

        # We are adding blocks in order, so the parent should be already in the blockchain.
        cumulative_difficulty = self.cumulative_difficulty[get_parent_key(block)] + block.difficulty
        self.cumulative_difficulty[get_key(block)] = cumulative_difficulty

        best_block_difficulty = self.cumulative_difficulty[get_key(self.best_block)]
        if cumulative_difficulty > best_block_difficulty:
            self.best_block = block

    def get_best_block(self):
        return self.best_block

    def get_block(self, hash):
        return self.blocks_by_hash[hash]

    def blocks_in_best_chain(self):
        block = self.best_block
        best_chain = set([get_key(block)])
        while not block == self.genesis:
            block = self.get_block(get_parent_key(block))
            best_chain.add(get_key(block))
        return best_chain

    def count_forks_depth(self):
        block_num = self.max_block_num
        visited = set()
        best_chain = self.blocks_in_best_chain()
        forks = {}
        while block_num > 0:
            blocks = self.blocks_by_number[block_num]
            blocks = filter(lambda x: (get_key(x) not in visited) and (get_key(x) not in best_chain), blocks)
            for block in blocks:
                visited.add(get_key(block))
                parent = self.get_block(get_parent_key(block))
                depth = 1
                while get_key(parent) not in best_chain:
                    visited.add(get_key(parent))
                    parent = self.get_block(get_parent_key(parent))
                    depth += 1
                if depth not in forks:
                    forks[depth] = 0
                forks[depth] += 1
            block_num -= 1
        return forks

    def count_repeated_blocks(self):
        forks = {}
        block_num = self.max_block_num
        while block_num > 0:
            n = len(self.blocks_by_number[block_num])
            if n not in forks:
                forks[n] = 0
            forks[n] += 1

            block_num -= 1
        return forks