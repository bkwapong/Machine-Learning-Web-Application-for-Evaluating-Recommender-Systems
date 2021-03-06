import math
import random
from collections import defaultdict
from operator import itemgetter

random.seed(0)


class UserBasedCF:
    ''' TopN recommendation - User Based Collaborative Filtering '''


    def __init__(self, n_sim_user = 20, n_rec_movie = 10):
        self.trainset = {}
        self.testset = {}

        self.n_sim_user = n_sim_user
        self.n_rec_movie = n_rec_movie

        self.user_sim_mat = {}
        self.movie_popular = {}
        self.movie_count = 0

        print ('Number of similar users to consider = %d' % self.n_sim_user)
        print ('Number of movies to recommend = %d\n' %
               self.n_rec_movie)

    @staticmethod
    def loadfile(filename):
        ''' load a file, return a generator. '''
        fp = open(filename, 'r')
        for i, line in enumerate(fp):
            yield line.strip('\r\n')
            if i % 100000 == 0:
                print ('loading %s(%s)')
        fp.close()
        print ('loaded %s succussfully')

    def generate_dataset(self, filename, pivot=0.7):
        ''' load rating data and split it to training set and test set '''
        trainset_len = 0
        testset_len = 0

        for line in self.loadfile(filename):
            user, movie, rating, _ = line.split('::')
            # split the data by pivot
            if random.random() < pivot:
                self.trainset.setdefault(user, {})
                self.trainset[user][movie] = int(rating)
                trainset_len += 1
            else:
                self.testset.setdefault(user, {})
                self.testset[user][movie] = int(rating)
                testset_len += 1
         ####testing
        assert (trainset_len != testset_len)
        shared_items = {k: self.trainset[k] for k in self.trainset if k in self.testset and self.trainset[k] == self.testset[k]}
        num_of_similar_items = (len(shared_items))

        print ('\n Number of items in both train and test set after initial split=%.4f' %
        (num_of_similar_items),file=outfile)
       # assert(self.trainset[user][movie] != self.testset[user][movie]).any()




    def calc_user_sim(self):
        ''' calculate user similarity matrix '''
        # build inverse table for item-users
        # key=movieID, value=list of userIDs who have seen this movie
        print ('\nbuilding movie-users inverse table...')
        movie2users = dict()

        for user, movies in self.trainset.items():
            for movie in movies:
                # inverse table for item-users
                if movie not in movie2users:
                    movie2users[movie] = set()
                movie2users[movie].add(user)
                # count item popularity at the same time
                if movie not in self.movie_popular:
                    self.movie_popular[movie] = 0
                self.movie_popular[movie] += 1
        print ('movie-users inverse table succussfully built')

        # save the total movie number, which will be used in evaluation
        self.movie_count = len(movie2users)
        print ('\ntotal movie number = %d' % self.movie_count)

        # count co-rated items between users
        usersim_mat = self.user_sim_mat
        print ('\nbuilding user co-rated movies matrix...')

        for movie, users in movie2users.items():
            for u in users:
                usersim_mat.setdefault(u, defaultdict(int))
                for v in users:
                    if u == v:
                        continue
                    usersim_mat[u][v] += 1
        print ('co-rated movies matrix succussfully built!')

        # calculate similarity matrix
        print ('\ncalculating user similarity matrix...')
        simfactor_count = 0
        PRINT_STEP = 2000000

        for u, related_users in usersim_mat.items():
            for v, count in related_users.items():
                usersim_mat[u][v] = count / math.sqrt(
                    len(self.trainset[u]) * len(self.trainset[v]))
                simfactor_count += 1
                if simfactor_count % PRINT_STEP == 0:
                    print ('calculating user similarity factor(%d)' %
                           simfactor_count)

        print ('calculation of user similarity matrix(similarity factor) done',
               )
        print ('\nTotal similarity factor number = %d' %
               simfactor_count)

    def recommend(self, user):
        ''' Find K similar users and recommend N movies. '''
        K = self.n_sim_user
        N = self.n_rec_movie
        rank = dict()
        watched_movies = self.trainset[user]

        for similar_user, similarity_factor in sorted(self.user_sim_mat[user].items(),
                                                      key=itemgetter(1), reverse=True)[0:K]:
            for movie in self.trainset[similar_user]:
                if movie in watched_movies:
                    continue
                # predict the user's "interest" for each movie
                rank.setdefault(movie, 0)
                rank[movie] += similarity_factor
        # return the N best movies
        return sorted(rank.items(), key=itemgetter(1), reverse=True)[0:N]

    def evaluate(self):
        ''' print evaluation result: precision, recall, coverage and popularity '''
        print ('\nEvaluating test and train set similarity')

        N = self.n_rec_movie
        #  varables for precision and recall
        hit = 0
        rec_count = 0
        test_count = 0
        # varables for coverage
        all_rec_movies = set()
        # varables for popularity
        popular_sum = 0

        for i, user in enumerate(self.trainset):
            if i % 500 == 0:
                print ('recommended for %d users')
            test_movies = self.testset.get(user, {})
            rec_movies = self.recommend(user)
            for movie, _ in rec_movies:
                if movie in test_movies:
                    hit += 1

                all_rec_movies.add(movie)

                popular_sum += math.log(1 + self.movie_popular[movie])
            rec_count += N
            test_count += len(test_movies)

        precision = round(hit / (1.0 * rec_count), 3)
        recall = round(hit / (1.0 * test_count), 3)
        coverage = round(len(all_rec_movies) / (1.0 * self.movie_count), 3)
        similar_items = len(all_rec_movies)
        popularity = popular_sum / (1.0 * rec_count)

        print ('\nprecision=%.4f\nrecall=%.4f\ncoverage=%.4f\npopularity=%.4f\nsimilaritems=%.4f' %
        (precision, recall, coverage, popularity,similar_items),file=outfile)

          #  print('\nTotal similar items = %d' %
               #   similar_items)






if __name__ == '__main__':
    # Dataset
    datafile = "/Users/ashleyfarrell/cs682.1/machinelearning/datasets/ratings100k.dat"
    #ratingfile = os.path.join('machinelearning', 'datasets', datafile)
    ratingfile =  datafile
    # open file to write output to
    outfile = open("unittest_results.txt", "w")
    # User input
    train_perc = float(.7)  # percentage of data to be used for training
    n_sim_users = int(10)  # number of similar users to consider
    n_movie_rec = int(10)  # number of movies to recommend to target users

    # Create object, calculate similarities for recommendation and evaluate
    for num_sim_users in [n_sim_users - 5, n_sim_users, n_sim_users + 5]:
        usercf = UserBasedCF()
        usercf.generate_dataset(ratingfile)
      #  outfile.close()
        usercf.calc_user_sim()
        usercf.evaluate()


    outfile.close()

